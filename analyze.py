import pickle
import shutil
import os
import subprocess

from matplotlib import pyplot
from collections import defaultdict, OrderedDict
import numpy as np

DATA_PATH = 'data/cleaned.pickle'


class Analyze:
    def __init__(self, serializer, data_path, charts_path='charts', html_path='index.html'):
        self.serializer = serializer
        self.data_path = data_path
        self.data = self.serializer.load(open(data_path, 'rb'))
        self.plot_count = 0
        self.bar_plot_config = {
            'color': '#539caf',
            'align': 'center',
            'width': 0.5
        }
        self.plot_figure_margins = {
            'bottom': 0.2
        }
        self.charts_path = charts_path
        self.html_path = html_path
        self.web_title = 'Politifact Analysis'
        shutil.rmtree(charts_path, ignore_errors=True)
        os.mkdir(charts_path)

    def build_charts(self):
        self._barchart(x='rating', title='Total Rating Counts', xlabel='Ratings', ylabel='Counts')
        self._barchart(
            group_by='affiliation',
            x='rating',
            title='Rating by Affiliation',
            xlabel='Ratings',
            ylabel='Counts'
        )
        self._barchart(
            group_by='affiliation',
            x='rating',
            percentage=True,
            title='Rating % by Affiliation',
            xlabel='Ratings',
            ylabel='Percentage'
        )
        self._write_html()
        self._open_html()
        # pyplot.show()

    def _barchart(self, group_by=None, x=None, percentage=False, title='Default', xlabel='Default', ylabel='Default'):
        ax = self._new_plot()
        if not group_by:
            counts = self._get_data(x, count=True)
            ax.bar(list(counts.keys()), list(counts.values()), **self.bar_plot_config)
            ax.set_xticklabels(list(counts.keys()), rotation=45, fontsize=8)
            ax.set_ylabel(ylabel)
            ax.set_xlabel(xlabel)
            ax.set_title(title)
        else:
            # Total width for all bars at one x location
            total_width = 0.9
            # Width of each individual bar
            x_data = self._get_data(x, group_by, count=True)
            groups = list(x_data.keys())
            ind_width = total_width / len(groups)
            # This centers each cluster of bars about the x tick mark
            alteration = np.arange(
                -(total_width / len(groups)),
                (total_width / len(groups)) + (ind_width / 2),
                ind_width
            )
            colors = ['#FF0000', '#0000FF', '#00FF00']

            # Draw bars, one category at a time
            for i in range(0, len(groups)):
                # Move the bar to the right on the x-axis so it doesn't
                # overlap with previously drawn ones
                if percentage:
                    total = sum(x_data[groups[i]].values())
                    data = [((i / total) * 100 if i else 0) for i in list(x_data[groups[i]].values())]
                else:
                    data = list(x_data[groups[i]].values())
                ax.bar(
                    range(len(list(x_data[groups[i]].keys()))) + alteration[i],
                    data,
                    color=colors[i],
                    label=groups[i],
                    width=ind_width
                )
            ax.set_xticks(list(np.arange(0, len(list(x_data[groups[i]].keys())), 1)))
            ax.set_xticklabels(list(x_data[groups[i]].keys()), rotation=45, fontsize=8)
            ax.set_ylabel(ylabel)
            ax.set_xlabel(xlabel)
            ax.set_title(title)
            ax.legend(loc='upper right')
        self._save_figure()

    def _save_figure(self):
        title = pyplot.gcf().gca().title.get_text().lower().replace(' ', '_') + '.png'
        pyplot.savefig(os.path.join(self.charts_path, title))

    def _new_plot(self):
        fig = pyplot.figure(self.plot_count)
        fig.subplots_adjust(**self.plot_figure_margins)
        ax = fig.add_subplot(111)
        self.plot_count += 1
        return ax

    def _get_data(self, key, group_by=None, count=False):
        if key is not None:
            if count:
                if not group_by:
                    counts = defaultdict(int)
                    for point in self.data:
                        counts[point[key]] += 1
                else:
                    group_bys = list(self._get_data(group_by, count=True).keys())
                    counts = {k: defaultdict(int) for k in group_bys}
                    for point in self.data:
                        counts[point[group_by]][point[key]] += 1
                        for other in counts.values():
                            if point[key] not in other:
                                other[point[key]] = 0
                counts = self._order_data(counts, key, 'rating', group_by)
                return counts

    def _order_data(self, data, key, order_by, group_by=None):
        if group_by is not None:
            final = OrderedDict()
            for group, inner_data in data.items():
                final[group] = OrderedDict()
                if order_by == 'rating':
                    final[group]['pants on fire!'] = inner_data['pants on fire!']
                    final[group]['false'] = inner_data['false']
                    final[group]['mostly false'] = inner_data['mostly false']
                    final[group]['half-true'] = inner_data['half-true']
                    final[group]['mostly true'] = inner_data['mostly true']
                    final[group]['true'] = inner_data['true']
                    final[group]['full flop'] = inner_data['full flop']
                    final[group]['half flip'] = inner_data['half flip']
                    final[group]['no flip'] = inner_data['no flip']
            return final
        return data


    def _write_html(self):
        html_file = f"<!doctype html><html><head><title>{self.web_title}</title></head><body>"
        for image in os.listdir(self.charts_path):
            full_path = os.path.join(self.charts_path, image)
            div = f"<div id='{full_path}'><img src='{full_path}'></div>"
            html_file += div + '<br>'
        html_file += "</body></html>"
        with open(self.html_path, 'w') as file:
            file.write(html_file)

    def _open_html(self):
        subprocess.Popen(["open", self.html_path])

a = Analyze(serializer=pickle, data_path=DATA_PATH)
a.build_charts()
