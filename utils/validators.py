import re
from datetime import datetime, date
from typing import Optional, List, Tuple


class ValidationError(Exception):
    pass


class Validators:
    """Клас для валідацій"""

    EMAIL_REGEX = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    NAME_REGEX = re.compile(r"^[а-яА-ЯіІїЇєЄa-zA-Z\s\-\']{2,50}$")

    @staticmethod
    def validate_email(email: str) -> bool:
        """Валідація email адреси"""
        return bool(Validators.EMAIL_REGEX.match(email))

    @staticmethod
    def validate_name(name: str) -> bool:
        """Валідація імені"""
        return bool(Validators.NAME_REGEX.match(name.strip()))

    @staticmethod
    def validate_birth_date(birth_date: str) -> Tuple[bool, Optional[date]]:
        """Валідація дати народження"""
        try:
            # Підтримка форматів DD.MM.YYYY, DD-MM-YYYY, DD/MM/YYYY
            for date_format in ["%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y"]:
                try:
                    parsed_date = datetime.strptime(
                        birth_date.strip(), date_format
                    ).date()

                    # Перевірка розумності дати
                    today = date.today()
                    if parsed_date > today:
                        return False, None

                    # Перевірка мінімального віку (наприклад, 16 років)
                    min_age_date = today.replace(year=today.year - 80)
                    max_age_date = today.replace(year=today.year - 16)

                    if (
                        parsed_date < min_age_date
                        or parsed_date > max_age_date
                    ):
                        return False, None

                    return True, parsed_date
                except ValueError:
                    continue

            return False, None

        except Exception:
            return False, None

    @staticmethod
    def validate_employee_data(
        first_name: str, last_name: str, email: str, birth_date: str
    ) -> List[str]:
        """Комплексна валідація даних співробітника"""
        
        errors = []

        if not Validators.validate_name(first_name):
            errors.append("Некоректне ім'я")

        if not Validators.validate_name(last_name):
            errors.append("Некоректне прізвище")

        if not Validators.validate_email(email):
            errors.append("Некоректна email адреса")

        is_valid_date, _ = Validators.validate_birth_date(birth_date)
        if not is_valid_date:
            errors.append("Некоректна дата народження")

        return errors
