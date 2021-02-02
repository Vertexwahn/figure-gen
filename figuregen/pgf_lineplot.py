from .element_data import *

import os
import tempfile
import subprocess
import shutil

class PgfLinePlot(Plot):
    def __init__(self, aspect_ratio, data, dpi=300, axis_lines="left") -> None:
        """Creates a line plot using LaTeX with the pgfplots package

        Arguments:
            aspect_ratio (float): Height/width ratio of the plotting area (used for alignment and grid sizing)
            data (list): A list of plot lines. Each element is a pair of two equal-sized lists: the x and y coordinates.
            axis_lines (str): Either "left" (arrows on the left and bottom always) or "middle" (arrows at 0 coordinate)
        """
        self.aspect_ratio = aspect_ratio
        self._data = data
        self._markers = {}
        self.set_font(7, "{libertine}")
        self.set_linewidth(0.8, 0.6)
        self._colors = [
            [232, 181, 88],
            [5, 142, 78],
            [94, 163, 188],
            [181, 63, 106],
            [20, 20, 20]
        ]
        self._labels = {}
        self.set_axis_label("x", "")
        self.set_axis_label("y", "")
        self._axis_properties = {}
        self.set_axis_properties("x", [], use_log_scale=False)
        self.set_axis_properties("y", [], use_log_scale=False)
        self.set_padding(5, 5)
        self._dpi = dpi
        self._axis_lines = axis_lines

    def get_colors(self):
        return self._colors

    def set_colors(self, color_list):
        '''
        color list contains a list of colors. A color is defined as [r,g,b] while each channel
        ranges from 0 to 255.
        '''
        self._colors = color_list

    def set_axis_label(self, axis, txt):
        self._labels[axis] = {}
        self._labels[axis]['text'] = txt.replace("\n", "\\\\{}")

    def set_axis_properties(self, axis, ticks, range=None, use_log_scale=True, use_scientific_notations=False):
        '''
        The user should find and define suitable ticks so that the labels and ticks don't overlap.
        Would be nice to do that automatically at some point.
        '''
        if range is not None and len(range) != 2:
            raise Error('You need exactly two values to specify range: [min, max]')

        self._axis_properties[axis] = {}
        if range is not None:
            self._axis_properties[axis]['range'] = range
        self._axis_properties[axis]['ticks'] = ticks
        self._axis_properties[axis]['use_log_scale'] = use_log_scale
        self._axis_properties[axis]['use_scientific_notations'] = use_scientific_notations

    def set_font(self, fontsize_pt=None, tex_package=None):
        if fontsize_pt is not None:
            self._fontsize_pt = fontsize_pt
        if tex_package is not None:
            self._font_tex_package = tex_package

    def set_linewidth(self, plot_line_pt=None, tick_line_pt=None):
        if plot_line_pt is not None:
            self._plot_linewidth_pt = plot_line_pt
        if tick_line_pt is not None:
            self._tick_linewidth_pt = tick_line_pt

    def set_padding(self, bottom_mm=None, left_mm=None):
        if bottom_mm is not None:
            self._pad_bot_mm = bottom_mm
        if left_mm is not None:
            self._pad_left_mm = left_mm

    def set_v_line(self, pos, color, linestyle=[], linewidth_pt=.8, phase_shift=0):
        ''' Adds a vertical line to the plot
            
        Args:
            color: the sRGB color of the line, each value in range [0, 255]
            linestyle: a list of dash lengths following the pattern: [on, off, on, off, ...].
                       An empty list corresponds to a solid line
            phase_shift: offset added to the dash pattern
        '''
        try:
            test = self._markers['vertical_lines'][0]
        except:
            self._markers['vertical_lines'] = []
        self._markers['vertical_lines'].append({
            'pos': pos,
            'color': color,
            "linestyle": linestyle,
            "linewidth_pt": linewidth_pt,
            "linephase": phase_shift,
        })

    def set_h_line(self, pos, color, linestyle=[], linewidth_pt=.8, phase_shift=0):
        ''' Adds a horizontal line to the plot
            Args:
                color: the sRGB color of the line, each value in range [0, 255]
                linestyle: a list of dash lengths following the pattern: [on, off, on, off, ...].
                           An empty list corresponds to a solid line
        '''
        try:
            test = self._markers['horizontal_lines'][0]
        except:
            self._markers['horizontal_lines'] = []
        self._markers['horizontal_lines'].append({
            'pos': pos,
            'color': color,
            "linestyle": linestyle,
            "linewidth_pt": linewidth_pt,
            "linephase": phase_shift,
        })

    @staticmethod
    def _compile_tex(tex, name, intermediate_dir = None):
        """ Compiles the given LaTeX code.

        Args:
            - tex   The file content of the LaTeX file to compile
            - name  Name of the output without the .pdf extension
            - intermediate_dir  Specify an existing directory here and .tex and .log files will be kept there
        """
        if intermediate_dir is not None and os.path.isdir(intermediate_dir):
            temp_folder = None
            temp_dir = os.path.abspath(intermediate_dir)
        else:
            temp_folder = tempfile.TemporaryDirectory()
            temp_dir = temp_folder.name

        with open(os.path.join(temp_dir, f"{os.path.basename(name)}.tex"), "w") as fp:
            fp.write(tex)

        subprocess.check_call(["pdflatex", "-interaction=nonstopmode", f"{os.path.basename(name)}.tex"],
            cwd=temp_dir, stdout=subprocess.DEVNULL)
        shutil.copy(os.path.join(temp_dir, f"{os.path.basename(name)}.pdf"), f"{name}.pdf")

        if temp_folder is not None:
            temp_folder.cleanup()

    def _ticks_to_str(self, axis):
        ticks = self._axis_properties[axis]['ticks']
        if ticks is None or len(ticks) == 0:
            return "\\empty"
        tick_str = [f"{t}" for t in ticks]
        return "{" + ",".join(tick_str) + "}"

    @staticmethod
    def _dash_pattern_to_str(pattern, phase):
        if pattern is None:
            return "{}"
        names = ["on", "off"]
        seq = "dash pattern = {"
        for i in range(len(pattern)):
            seq += f"{names[i % 2]} {pattern[i]} "
        seq += "},"
        phase = "dash phase = {" + str(phase) + "},"
        return seq + phase

    def _clip_ticks(self, axis):
        # Ensure that all ticks fall within the range, otherwise LaTeX will not compile
        if 'range' in self._axis_properties[axis]:
            if self._axis_properties[axis]['ticks'] is not None:
                clipped = []
                for t in self._axis_properties[axis]['ticks']:
                    if t > self._axis_properties[axis]['range'][0] and t < self._axis_properties[axis]['range'][1]:
                        clipped.append(t)
                self._axis_properties[axis]['ticks'] = clipped

    def _clean(self):
        self._clip_ticks("x")
        self._clip_ticks("y")

    def _make_tex(self, width, height):
        self._clean()

        tex_code = ""

        preamble_lines = [
            "\\documentclass{article}",
            "\\pagenumbering{gobble}",
            "\\usepackage{xcolor}",
            "\\usepackage{graphicx}",
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage[T1]{fontenc}",
            "\\usepackage{geometry}",
            "\\usepackage{tikz}",
            "\\usepackage{pgfplots}",
            "\\pgfplotsset{compat=newest}",

            "\\usepackage" + self._font_tex_package,

            "\\newcommand{\\width}{" + f"{width}mm" + "}",
            "\\newcommand{\\height}{" + f"{height}mm" + "}",
            "\\newcommand{\\padbot}{" + f"{self._pad_bot_mm}mm" + "}",
            "\\newcommand{\\padleft}{" + f"{self._pad_left_mm}mm" + "}",

            "\\geometry{",
            "    papersize={\\width,\\height},",
            "    total={\\width,\\height},",
            "    left=0mm,",
            "    top=0mm,",
            "}",

            "\\makeatletter \\newcommand{\\pgfplotsdrawaxis}{\\pgfplots@draw@axis} \\makeatother",
            "\\pgfplotsset{axis line on top/.style={",
            "axis line style=transparent,",
            "ticklabel style=transparent,",
            "tick style=transparent,",
            "axis on top=false,",
            "after end axis/.append code={",
            "    \\pgfplotsset{axis line style=opaque,",
            "    ticklabel style=opaque,",
            "    tick style=opaque,",
            "    grid=none}",
            "    \\pgfplotsdrawaxis}",
            "  }",
            "}",
        ]

        if self._colors is not None:
            i = 0
            for clr in self._colors:
                preamble_lines.append("\\definecolor{color" + f"{i}" + "}{RGB}{"
                    + f"{clr[0]},{clr[1]},{clr[2]}" + "}")
                i += 1

        if 'vertical_lines' in self._markers:
            i = 0
            for m in self._markers['vertical_lines']:
                clr = m["color"]
                preamble_lines.append("\\definecolor{vertlinecolor" + f"{i}" + "}{RGB}{"
                    + f"{clr[0]},{clr[1]},{clr[2]}" + "}")
                i += 1

        if 'horizontal_lines' in self._markers:
            i = 0
            for m in self._markers['horizontal_lines']:
                clr = m["color"]
                preamble_lines.append("\\definecolor{horzlinecolor" + f"{i}" + "}{RGB}{"
                    + f"{clr[0]},{clr[1]},{clr[2]}" + "}")
                i += 1
        preamble_lines.append("\\definecolor{gridcolor}{RGB}{220,220,220}")

        tex_code += "\n".join(preamble_lines) + "\n"

        body_start_lines = [
            "\\begin{document}",
            "\\raggedleft",
            "\\begin{tikzpicture}[trim axis left]",
            "\\clip (-\\padleft,-\\padbot) rectangle (\\width-\\padleft, \\height-\\padbot);",
            "\\begin{axis}[",
            "    scale only axis,",
            "    height=\\height-\\padbot,",
            "    width=\\width-\\padleft,",
            f"    axis lines = {self._axis_lines},",
            "    xlabel near ticks,",
            "    xlabel={" + self._labels["x"]["text"] + "},",
            "    ylabel={" + self._labels["y"]["text"] + "},",
            f"    xtick={self._ticks_to_str('x')},",
            f"    ytick={self._ticks_to_str('y')},",
            "    yminorticks=false,",
            "    xminorticks=false,",
            "    yticklabel style={inner sep=1pt},", # distance between y tick labels and the marker
            "    xticklabel style={inner sep=1pt},", # distance between x tick labels and the marker
            "    legend pos=north west,",
            "    ymajorgrids=true,",
            "    xmajorgrids=true,",
            "    grid style={solid, line width=0.25pt, gridcolor},",
            "    axis line on top,",
            "    xlabel style={",
            "        inner sep=3pt,",
            "        at={(ticklabel* cs:1.05)}, anchor=north east,",
            "        text width=\\width,",
            "        align=right,",
            "    },",
            "    ylabel style={",
            "        inner sep=3pt,",
            "        at={(ticklabel* cs:1.05)}, anchor=south east, ",
            "        rotate=0,",
            "        text width=\\height,",
            "        align=right,",
            "    },",
            "    label style={",
            "        font=\\fontsize{" + f"{self._fontsize_pt}" + "pt}{" + f"{self._fontsize_pt}" + "pt}\\selectfont",
            "    },",
            "    tick label style={",
            "        font=\\fontsize{" + f"{self._fontsize_pt}" + "pt}{" + f"{self._fontsize_pt}" + "pt}\\selectfont",
            "    },",
            f"    line width={self._plot_linewidth_pt}pt,",
            "    axis line style={line width=" + f"{self._tick_linewidth_pt}" + "pt},",
            "    tick style={",
            f"        line width={self._tick_linewidth_pt}pt,",
            "        color=black",
            "    },",
            "    x tick label style={",
            "        /pgf/number format/.cd,",
            "        scaled x ticks = false,",
            "        fixed," if not self._axis_properties["x"]['use_scientific_notations'] else "",
            "        /tikz/.cd",
            "    },",
            "    y tick label style={",
            "        /pgf/number format/.cd,",
            "        scaled y ticks = false,",
            "        fixed," if not self._axis_properties["y"]['use_scientific_notations'] else "",
            "        /tikz/.cd",
            "    },",
        ]

        if not self._axis_properties["x"]['use_scientific_notations']:
            body_start_lines.append("    log ticks with fixed point,")

        if 'range' in self._axis_properties['x']:
            body_start_lines.append(f"    xmin={self._axis_properties['x']['range'][0]}, xmax={self._axis_properties['x']['range'][1]},")
            # body_start_lines.append(f"    restrict x to domain={self._axis_properties['x']['range'][0]}:{self._axis_properties['x']['range'][1]},")
        if 'range' in self._axis_properties['y']:
            body_start_lines.append(f"    ymin={self._axis_properties['y']['range'][0]}, ymax={self._axis_properties['y']['range'][1]},")
            # body_start_lines.append(f"    restrict y to domain={self._axis_properties['y']['range'][0]}:{self._axis_properties['y']['range'][1]},")

        if self._axis_properties["x"]['use_log_scale']:
            body_start_lines.append("    xmode=log,")
        if self._axis_properties["y"]['use_log_scale']:
            body_start_lines.append("    ymode=log,")

        body_start_lines.append("]")
        tex_code += "\n".join(body_start_lines) + "\n"

        # Add the actual plot lines
        for line_idx in range(len(self._data)):
            plot_code = [
                "\\addplot[",
                f"    color=color{line_idx}" if self._colors is not None and len(self._colors) > line_idx else "",
                "]",
                "coordinates {",
            ]
            coords = ""
            for i in range(len(self._data[line_idx][0])):
                x = self._data[line_idx][0][i]
                y = self._data[line_idx][1][i]
                coords += f"({x},{y})"
            plot_code.append(coords)
            plot_code.append("};")
            tex_code += "\n".join(plot_code) + "\n"

        # Add vertical and horizontal markers
        if "vertical_lines" in self._markers:
            i = 0
            for m in self._markers["vertical_lines"]:
                codelines = [
                    "\\draw[",
                    f"  vertlinecolor{i},",
                    f"  line width={m['linewidth_pt']}pt,",
                    self._dash_pattern_to_str(m["linestyle"], m["linephase"]),
                    "]",
                    "({axis cs:" + f"{m['pos']}" + ",0}|-{rel axis cs:0,1}) -- ({axis cs:"
                        + f"{m['pos']}" + ",0}|-{rel axis cs:0,0});"
                ]
                tex_code += "\n".join(codelines) + "\n"
                i += 1
        if "horizontal_lines" in self._markers:
            i = 0
            for m in self._markers["horizontal_lines"]:
                codelines = [
                    "\\draw[",
                    f"  horzlinecolor{i},",
                    f"  line width={m['linewidth_pt']}pt,",
                    self._dash_pattern_to_str(m["linestyle"], m["linephase"]),
                    "]",
                    "({rel axis cs:1,0}|-{axis cs:0," + f"{m['pos']}" +
                        "}) -- ({rel axis cs:0,0}|-{axis cs:0," + f"{m['pos']}" + "});"
                ]
                tex_code += "\n".join(codelines) + "\n"
                i += 1

        body_end_lines = [
            "\\end{axis}",
            "\\end{tikzpicture}",
            "\\end{document}",
        ]
        tex_code += "\n".join(body_end_lines) + "\n"

        return tex_code

    def make_pdf(self, width, height, filename):
        tex = self._make_tex(width, height)
        self._compile_tex(tex, filename)
        return filename + ".pdf"

    def make_raster(self, width, height, filename):
        fn = self.make_pdf(width, height, filename)
        from pdf2image import convert_from_path
        convert_from_path(fn, dpi=self._dpi, transparent=True, fmt="png", output_file=filename, single_file=True)
        return filename + ".png"