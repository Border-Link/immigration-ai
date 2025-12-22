class Normalizer:

    def nomalize(self, file):
        import csv
        from io import StringIO

        data = []
        file.open()
        decoded_file = file.read().decode('utf-8')
        reader = csv.DictReader(StringIO(decoded_file))

        for row in reader:
            row_normalized = {key.strip().lower(): value.strip() for key, value in row.items()}
            data.append(row_normalized)

        return data