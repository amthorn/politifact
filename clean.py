import pickle
import datetime

RAW_DATA_PATH = 'data/results.pickle'


class Clean():
    def __init__(self, serializer, raw_path):
        self.serializer = serializer
        self.raw_path = raw_path
        self.raw = serializer.load(open(self.raw_path, 'rb'))
        self.output_path = 'data/cleaned.pickle'

    def clean(self):
        flat = []
        # Flatten data
        for point in self.raw:
            if isinstance(point, (list, tuple)):
                for instance in point:
                    flat.append(instance)
            else:
                flat.append(instance)
        assert all([isinstance(i, dict) for i in flat]), \
            "Data not in appropriate format, structures deeper than list of list of dict discovered"

        # Remove duplicate entries and add sequential IDs
        cleaned = []
        duplicates = []
        count = 0
        # O(n^2)
        for point in flat:
            point['date'] = self._format_date(point['date'])
            point['edition'] = self._format_edition(point['edition'])
            point['rating'] = self._format_rating(point['rating'])
            duplicate = self._contains_entry(cleaned, point)
            if not duplicate:
                cleaned.append({**point, **{'id': count}})
            else:
                # In case of duplicates, append one with the latest date since politifact can
                # Reanalyze claims. Most recent one matters; older ones are ignored
                actual = self._get_later(point, duplicate)
                duplicates.append([point, duplicate])
                if 'id' not in actual:
                    cleaned.append({**actual, **{'id': duplicate['id']}})
            count += 1


        assert all(['id' in i for i in cleaned]), \
            "Data was not cleaned appropriately, duplicate entry mistakenly retained"

        print(len(flat) - len(cleaned), 'duplicate entries removed')

        self.cleaned = cleaned
        return self.cleaned

    def _contains_entry(self, data, entry):
        # O(n)
        keys = ['text', 'source']
        for point in data:
            if all([entry[i] == point[i] for i in keys]):
                return point
        else:
            return None

    def _get_later(self, point, duplicate):
        if point['date'] - duplicate['date'] > datetime.timedelta(0):
            return point
        else:
            return duplicate

    def _format_date(self, date):
        suffixes = ['st', 'nd', 'rd', 'th']
        # O(n)
        for suffix in suffixes:
            try:
                return datetime.datetime.strptime(date, f'on %A, %B %d{suffix}, %Y')
            except ValueError:
                pass

    def _format_edition(self, edition):
        return edition.replace("— ", "", 1)

    def _format_rating(self, rating):
        return rating.lower()

    def write(self):
        self.serializer.dump(self.cleaned, open(self.output_path, 'wb'))

c = Clean(serializer=pickle, raw_path=RAW_DATA_PATH)
c.clean()
c.write()
