from datetime import timedelta, datetime, date, time

from dateutil.relativedelta import relativedelta
from django.utils.timezone import now
from rest_framework import serializers


class DateHelper:

    @staticmethod
    def make_timezone_aware(value):
        """
        Converts a date or datetime value to a timezone-aware datetime.
        If the value is a date, it combines it with the minimum time to create a datetime.
        If the value is a naive datetime, it makes it timezone-aware.
        Returns None if the value is None.
        """
        from django.utils import timezone
        if value is None:
            return None
        value = datetime.combine(value, time.min) if isinstance(value, date) else value
        if isinstance(value, datetime) and timezone.is_naive(value):
            return timezone.make_aware(value)
        return value


    @staticmethod
    def add_days(date, days):
        return date + timedelta(days=days)

    @staticmethod
    def subtract_days(date, days):
        return date - timedelta(days=days)

    @staticmethod
    def get_today():
        return now().date()

    @staticmethod
    def start_of_month():
        today = now().date()
        return today.replace(day=1)

    @staticmethod
    def one_month_from_date(start_date):
        return start_date + relativedelta(months=1)


    @staticmethod
    def create_start_end_date():
        today = now().date()
        start_date = today.replace(day=1)
        end_date = today
        return start_date, end_date

    @staticmethod
    def create_start_end_date_one_month():
        end_date = now().date()
        start_date = end_date - relativedelta(months=1)
        return start_date, end_date

    @staticmethod
    def to_date(value):
        """
        Converts a value to a date object. Accepts date, datetime, or string.
        Handles naive datetimes by making them timezone-aware if needed.
        Returns None if value is None or cannot be converted.
        """
        from django.utils import timezone
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            if timezone.is_naive(value):
                value = timezone.make_aware(value)
            return value.date()
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
                try:
                    dt = datetime.strptime(value, fmt)
                    if timezone.is_naive(dt):
                        dt = timezone.make_aware(dt)
                    return dt.date()
                except ValueError:
                    continue
        return None

    @staticmethod
    def one_year_from_date(start_date):
        """
        Returns a date one year from the given start date.
        If start_date is None, returns None.
        """
        if start_date is None:
            return None
        return start_date + relativedelta(years=1)


    @staticmethod
    def six_month_from_date(start_date):
        """
        Returns a date six months from the given start date.
        If start_date is None, returns None.
        """
        if start_date is None:
            return None
        return start_date + relativedelta(months=6)


    @staticmethod
    def three_month_from_date(start_date):
        """
        Returns a date three months from the given start date.
        If start_date is None, returns None.
        """
        if start_date is None:
            return None
        return start_date + relativedelta(months=3)

    @staticmethod
    def one_year_ago():
        """
        Returns the date one year ago from today.
        """
        return now().date() - relativedelta(years=1)

    @staticmethod
    def six_month_ago():
        """
        Returns the date six months ago from today.
        """
        return now().date() - relativedelta(months=6)


    @staticmethod
    def three_month_ago():
        """
        Returns the date three months ago from today.
        """
        return now().date() - relativedelta(months=3)

    @staticmethod
    def one_month_ago():
        """
        Returns the date one month ago from today.
        """
        return now().date() - relativedelta(months=1)

class DateValidator:
    @staticmethod
    def validate_start_date(start_date):
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

        if start_date and start_date > date.today():
            raise serializers.ValidationError("Start date cannot be in the future.")
        return start_date

    @staticmethod
    def validate_future_start_date(start_date):
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

        if start_date and start_date < date.today():
            raise serializers.ValidationError("Start date cannot be in the past.")
        return start_date

    @staticmethod
    def validate_end_date(start_date, end_date):
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

        if end_date and end_date < start_date:
            raise serializers.ValidationError("End date cannot be before start date.")
        return end_date

    @staticmethod
    def validate_year(year):
        current_year = date.today().year
        if year < 1900 or year > current_year:
            raise serializers.ValidationError("Year must be between 1900 and the current year.")
        return year
