from calendar import monthcalendar
from datetime import date, datetime, timedelta
from typing import List, Self, Dict

from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pytz import utc

from app.bot.classes.button_factory import ButtonFactory
from app.bot.scenes.callback_data import CalendarDayChoiceAction, CalendarConfirmAction


class Calendar:
    __weekdays: List[str] = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
    __months: List[str] = [
        "Січень",
        "Лютий",
        "Березень",
        "Квітень",
        "Травень",
        "Червень",
        "Липень",
        "Серпень",
        "Вересень",
        "Жовтень",
        "Листопад",
        "Грудень"
    ]

    def __init__(
            self,
            *,
            year: int | None = None,
            month: int | None = None,
            selected_days: List[date] | None = None,
            select_limit: int = 5
    ) -> None:
        self.now: date = datetime.now(utc).date()

        if year is None:
            self.year: int = self.now.year
        else:
            self.year: int = year

        if month is None:
            self.month: int = self.now.month
        else:
            self.month: int = month

        if selected_days is None:
            self.__selected_days = []
        else:
            self.__selected_days = selected_days

        self.select_limit: int = select_limit

    @property
    def selected_days(self) -> List[date]:
        return list(sorted(self.__selected_days))

    @classmethod
    async def from_state(
            cls,
            state: FSMContext
    ) -> Self | None:
        calendar_data: Dict[str, str | int | list] = (await state.get_data()).get("calendar")

        if calendar_data is None:
            return

        year: int = calendar_data.get("year")
        month: int = calendar_data.get("month")
        selected_days: List[date] = cls.deserialize_days(calendar_data.get("days"))
        select_limit: int = calendar_data.get("limit")

        return cls(year=year, month=month, selected_days=selected_days, select_limit=select_limit)

    async def to_state(
            self,
            state: FSMContext
    ) -> None:
        calendar_data: Dict[str, int] = {
            "year": self.year,
            "month": self.month,
            "days": self.serialize_days(self.__selected_days),
            "limit": self.select_limit
        }

        await state.update_data(calendar=calendar_data)

    def add(
            self,
            months: int
    ) -> None:
        calendar_date: date = date(year=self.year, month=self.month, day=1)
        sign: int = months // abs(months)

        for _ in range(abs(months)):
            calendar_date += timedelta(days=sign)
            while calendar_date.day != 1:
                calendar_date += timedelta(days=sign)

        self.year = calendar_date.year
        self.month = calendar_date.month

    def select(
            self,
            day: date
    ) -> bool:
        for selected_day in self.__selected_days:
            if selected_day.year == day.year and selected_day.month == day.month and selected_day.day == day.day:
                self.__selected_days.remove(selected_day)
                return True

        if len(self.__selected_days) >= self.select_limit:
            return False

        self.__selected_days.append(day)
        return True

    def as_markup(
            self,
            i18n: I18n,
            button_factory: ButtonFactory,
            with_confirm: bool = False
    ) -> InlineKeyboardMarkup:
        builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
        calendar_data: List[List[int]] = monthcalendar(self.year, self.month)

        with i18n.context():
            builder.button(
                text=_("calendar.month_info").format(year=self.year, month=self.__months[self.month - 1]),
                callback_data=CalendarDayChoiceAction(day=0).pack()
            )

            builder.row(
                *[
                    InlineKeyboardButton(
                        text=self.__weekdays[day],
                        callback_data=CalendarDayChoiceAction(day=0).pack()
                    ) for day in range(7)
                ],
                width=7
            )

            for row in calendar_data:
                builder.row(
                    *[
                        InlineKeyboardButton(
                            text=self.__get_day(day),
                            callback_data=CalendarDayChoiceAction(year=self.year, month=self.month, day=day).pack()
                        )
                        for day in row
                    ],
                    width=7
                )

            builder.row(*button_factory.create_pagination_buttons(), width=2)
            if with_confirm:
                builder.row(
                    InlineKeyboardButton(
                        text=_("button.confirm_selected_days"),
                        callback_data=CalendarConfirmAction().pack()
                    ),
                    width=1
                )
            builder.row(button_factory.create_back_button(), width=1)

        return builder.as_markup()

    def __get_day(
            self,
            day: int
    ) -> str:
        if not day:
            return " "

        for selected_day in self.__selected_days:
            if selected_day.day == day and selected_day.month == self.month and selected_day.year == self.year:
                return "✅"

        if day == self.now.day and self.month == self.now.month and self.year == self.now.year:
            return "📍"

        return str(day)

    @staticmethod
    def serialize_days(days: List[date], date_format: str = "%Y-%m-%d") -> List[str]:
        return list(map(lambda day: day.strftime(date_format), days))

    @staticmethod
    def deserialize_days(days: List[str], date_format: str = "%Y-%m-%d") -> List[date]:
        return list(map(lambda day: datetime.strptime(day, date_format), days))
