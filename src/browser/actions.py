"""
Действия в браузере.

Реализует:
- Навигация по hh.ru
- Клик по кнопкам (отклик, пагинация)
- Скролл страницы
- Заполнение форм
- Обработка модальных окон
"""

import random
import asyncio
import logging
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from src.browser.anti_detect import AntiDetect

logger = logging.getLogger(__name__)


class BrowserActions:
    """
    Действия в браузере с анти-детект мерами.
    """

    def __init__(self, page: Page):
        self.page = page
        self.anti_detect = AntiDetect()

    async def goto(self, url: str, wait_until: str = "domcontentloaded"):
        """
        Переход на URL с анти-детект задержкой.
        """
        await self.page.goto(url, wait_until=wait_until, timeout=20000)
        await self.anti_detect.random_delay(0.1, 0.3)

    async def scroll_to_bottom(self):
        """
        Плавно скроллит страницу до конца.
        """
        await self.page.evaluate("""
            async () => {
                const distance = document.body.scrollHeight - window.innerHeight;
                const steps = 10;
                const step = distance / steps;
                
                for (let i = 0; i < steps; i++) {
                    window.scrollBy(0, step);
                    await new Promise(r => setTimeout(r, 100 + Math.random() * 200));
                }
            }
        """)
        await self.anti_detect.random_delay()

    async def click_vacancy(self, vacancy_index: int = 0) -> bool:
        """
        Кликает на вакансию в результатах поиска.
        """
        try:
            vacancies = self.page.locator('[data-qa="search-result-item"]')
            await vacancies.nth(vacancy_index).click()
            await self.anti_detect.random_delay()
            return True
        except Exception as e:
            logger.error(f"Ошибка клика по вакансии: {e}")
            return False

    async def click_apply_button(self, vacancy_index: int = 0) -> dict:
        """
        Кликает кнопку «Откликнуться» в карточке вакансии.

        Returns:
            dict с результатом:
            - success: bool
            - needs_letter: bool (требуется письмо)
            - has_questions: bool (есть вопросы)
            - error: str (ошибка)
        """
        try:
            # hh.ru показывает форму "Напишите телефон" — закрываем её
            phone_form_selectors = [
                '[data-qa="phone-number-form"] button[data-qa="close"]',
                'button[data-qa="phone-number-form-skip"]',
                'button:has-text("Продолжить без телефона")',
                'button:has-text("Пропустить")',
                # Кнопка "Продолжить" в форме телефона ведёт дальше без ввода
            ]
            for sel in phone_form_selectors:
                loc = self.page.locator(sel)
                if await loc.count() > 0:
                    await loc.click()
                    logger.debug(f"Закрыта форма телефона: {sel}")
                    await self.page.wait_for_timeout(1000)
                    break

            apply_selectors = [
                '[data-qa="vacancy-response"]',
                '[data-qa="vacancy-response-link"]',
                '[data-qa="vacancy-response-popup-button"]',
                'a[href*="applicant/vacancy_response"]',
                'button[data-qa*="response"]',
                '[class*="vacancy-response-button"]',
                'button:has-text("Откликнуться")',
            ]
            apply_btn = None
            for sel in apply_selectors:
                loc = self.page.locator(sel).nth(vacancy_index)
                if await loc.count() > 0:
                    apply_btn = loc
                    logger.debug(f"Кнопка отклика найдена: {sel}")
                    break

            if apply_btn is None:
                return {"success": False, "error": "Кнопка отклика не найдена"}

            await apply_btn.click()
            await self.anti_detect.random_delay()

            # Ждём реакцию страницы — до 5 сек
            await self.page.wait_for_timeout(5000)

            # Скриншот для диагностики (перезаписывается каждый раз)
            try:
                await self.page.screenshot(path="apply_debug.png")
                logger.info(
                    f"Скриншот после клика: apply_debug.png | URL: {self.page.url}"
                )
            except Exception:
                pass

            # 1. Модальное окно с письмом
            letter_selectors = [
                '[data-qa="cover-letter-modal"]',
                '[data-qa="vacancy-response-popup"]',
                '[data-qa="vacancy-response-letter-toggle"]',
                'textarea[data-qa*="letter"]',
                'textarea[placeholder*="письм"]',
                'textarea[placeholder*="Напишите"]',
                'textarea[placeholder*="сопроводительн"]',
                ".vacancy-response-letter",
                # hh.ru 2025-2026
                '[class*="applicant-response"] textarea',
                'div[class*="response-popup"] textarea',
            ]
            for sel in letter_selectors:
                if await self.page.locator(sel).count() > 0:
                    logger.debug(f"Найдено поле письма: {sel}")
                    return {
                        "success": False,
                        "needs_letter": True,
                        "has_questions": False,
                    }

            # 2. Вопросы от работодателя
            question_selectors = [
                '[data-qa="vacancy-questions"]',
                '[data-qa="applicant-questions"]',
                ".vacancy-questions",
                '[class*="employer-questions"]',
            ]
            for sel in question_selectors:
                if await self.page.locator(sel).count() > 0:
                    return {
                        "success": False,
                        "needs_letter": False,
                        "has_questions": True,
                    }

            # 3. Кнопка уже нажата / отклик отправлен (кнопка стала "Отклик отправлен")
            sent_selectors = [
                '[data-qa="vacancy-response-letter-confirm"]',
                'button:has-text("Отклик отправлен")',
                'button:has-text("Вы откликнулись")',
                '[class*="response-button--applied"]',
                # hh.ru 2025-2026: кнопка меняет текст
                'button:has-text("Отклик направлен")',
                'button:has-text("Вы уже откликнулись")',
                '[data-qa="vacancy-response-completed"]',
            ]
            for sel in sent_selectors:
                if await self.page.locator(sel).count() > 0:
                    return {
                        "success": True,
                        "needs_letter": False,
                        "has_questions": False,
                    }

            # 4. Snackbar / toast с подтверждением
            snackbar_selectors = [
                '[data-qa="snackbar"]',
                '[class*="snackbar"]',
                '[data-qa="bloko-notification"]',
                '[class*="toast"]',
            ]
            for sel in snackbar_selectors:
                loc = self.page.locator(sel).first
                if await loc.count() > 0:
                    try:
                        text = await loc.inner_text()
                    except Exception:
                        text = ""
                    if any(w in text.lower() for w in ["отклик", "отправ", "успешно"]):
                        return {
                            "success": True,
                            "needs_letter": False,
                            "has_questions": False,
                        }

            # 5. Редирект на страницу отклика
            if any(w in self.page.url.lower() for w in ["response", "negotiations"]):
                return {"success": True, "needs_letter": False, "has_questions": False}

            # 6. Модальное окно подтверждения без textarea — кнопка "Откликнуться" внутри модалки
            # (hh.ru 2025+: диалог с выбором резюме, без поля письма)
            # Также: bloko-notification с кнопкой "Откликнуться" и "Закрыть"
            modal_confirm_selectors = [
                '[data-qa="vacancy-response-popup-button"]',
                '[data-qa="bloko-notification"] button:has-text("Откликнуться")',
                '.bloko-notification button:has-text("Откликнуться")',
                '[role="dialog"] button:has-text("Откликнуться")',
                '[role="dialog"] button[data-qa*="submit"]',
                '[role="dialog"] button[data-qa*="response"]',
                'div[class*="modal"] button:has-text("Откликнуться")',
                'div[class*="popup"] button:has-text("Откликнуться")',
            ]
            for sel in modal_confirm_selectors:
                loc = self.page.locator(sel)
                if await loc.count() > 0:
                    logger.info(f"Найден диалог подтверждения: {sel} — кликаем")
                    await loc.click()
                    await self.page.wait_for_timeout(4000)

                    # Проверяем успех после второго клика
                    for sent_sel in sent_selectors:
                        if await self.page.locator(sent_sel).count() > 0:
                            return {
                                "success": True,
                                "needs_letter": False,
                                "has_questions": False,
                            }
                    for snack_sel in snackbar_selectors:
                        snack_loc = self.page.locator(snack_sel).first
                        if await snack_loc.count() > 0:
                            try:
                                snack_text = await snack_loc.inner_text()
                            except Exception:
                                snack_text = ""
                            if any(
                                w in snack_text.lower()
                                for w in ["отклик", "отправ", "успешно"]
                            ):
                                return {
                                    "success": True,
                                    "needs_letter": False,
                                    "has_questions": False,
                                }
                    if any(
                        w in self.page.url.lower() for w in ["response", "negotiations"]
                    ):
                        return {
                            "success": True,
                            "needs_letter": False,
                            "has_questions": False,
                        }

                    # Если после клика модалка пропала — считаем успехом
                    if await self.page.locator(sel).count() == 0:
                        return {
                            "success": True,
                            "needs_letter": False,
                            "has_questions": False,
                        }

                    break

            # 7. Пагинация страницы не поменялась — делаем финальный скриншот
            try:
                await self.page.screenshot(path="apply_debug_final.png")
                logger.warning(
                    f"Неизвестный результат. URL: {self.page.url} | Скриншот: apply_debug_final.png"
                )
            except Exception:
                pass

            return {"success": False, "error": "Неизвестный результат отклика"}

        except Exception as e:
            logger.error(f"Ошибка отклика: {e}")
            return {"success": False, "error": str(e)}

    async def fill_cover_letter(self, letter: str) -> bool:
        """
        Заполняет и отправляет сопроводительное письмо в модальном окне.

        Returns:
            True если отклик отправлен успешно
        """
        try:
            # Ждём появления поля письма до 5 сек
            input_selectors = [
                '[data-qa="cover-letter-input"]',
                'textarea[data-qa*="letter"]',
                'textarea[placeholder*="письм"]',
                'textarea[placeholder*="Напишите"]',
                'textarea[placeholder*="сопроводительн"]',
                ".vacancy-response-letter textarea",
                '[class*="applicant-response"] textarea',
                'div[class*="response-popup"] textarea',
            ]
            letter_input = None
            for sel in input_selectors:
                loc = self.page.locator(sel)
                try:
                    await loc.wait_for(timeout=5000)
                    letter_input = loc
                    logger.debug(f"Поле письма найдено: {sel}")
                    break
                except Exception:
                    continue

            if letter_input is None:
                logger.error("Поле для письма не найдено")
                return False

            # Очищаем и заполняем
            await letter_input.click()
            await letter_input.fill("")
            await letter_input.fill(letter)
            await self.anti_detect.random_delay()

            # Проверяем что текст реально вставился
            filled = await letter_input.input_value()
            if not filled.strip():
                logger.error("Текст письма не вставился в поле")
                return False

            # Кнопка отправки — только специфичные селекторы, не button[type=submit]
            submit_selectors = [
                '[data-qa="cover-letter-submit"]',
                '[data-qa="vacancy-response-submit"]',
                '[data-qa="vacancy-response-letter-submit"]',
                'button[data-qa*="submit"]',
                # hh.ru 2025-2026
                'button:has-text("Откликнуться")',
                'button:has-text("Отправить")',
                '[class*="response-popup"] button[class*="primary"]',
                '[class*="applicant-response"] button[class*="primary"]',
            ]
            submit_btn = None
            for sel in submit_selectors:
                loc = self.page.locator(sel)
                if await loc.count() > 0:
                    submit_btn = loc
                    logger.debug(f"Кнопка отправки найдена: {sel}")
                    break

            if submit_btn is None:
                logger.error("Кнопка отправки не найдена")
                return False

            await submit_btn.click()

            # Ждём подтверждение до 8 сек
            success_selectors = [
                '[data-qa="snackbar"]',
                '[class*="snackbar"]',
                '[class*="notification"]',
                '[class*="toast"]',
                'button:has-text("Отклик отправлен")',
                'button:has-text("Вы откликнулись")',
            ]
            combined = ", ".join(success_selectors)
            try:
                await self.page.wait_for_selector(combined, timeout=8000)
                logger.info("Отклик с письмом отправлен успешно")
                return True
            except PlaywrightTimeout:
                # Snackbar не появился — проверяем URL
                if any(
                    w in self.page.url.lower() for w in ["response", "negotiations"]
                ):
                    logger.info("Отклик отправлен (редирект)")
                    return True
                logger.warning("Не удалось подтвердить отправку отклика")
                return False

        except Exception as e:
            logger.error(f"Ошибка заполнения письма: {e}")
            return False

    async def search_vacancies(self, query: str, filters: dict = None) -> bool:
        """
        Выполняет поиск вакансий.
        """
        try:
            # Переходим на hh.ru
            await self.goto("https://hh.ru/search/vacancy")

            # Находим поле поиска
            search_input = self.page.locator('[data-qa="search-bar-input"]')
            await search_input.fill(query)
            await self.anti_detect.random_delay()

            # Нажимаем Enter или кнопку поиска
            await self.page.keyboard.press("Enter")
            await self.anti_detect.random_delay()

            # Ждём результаты
            await self.page.wait_for_selector(
                '[data-qa="search-result-item"]', timeout=15000
            )

            return True
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return False

    async def navigate_to_resumes(self) -> bool:
        """Переход на страницу резюме."""
        try:
            await self.goto("https://hh.ru/resume/mine")
            return True
        except Exception as e:
            logger.error(f"Ошибка навигации к резюме: {e}")
            return False

    async def navigate_to_applications(self) -> bool:
        """Переход на страницу откликов."""
        try:
            await self.goto("https://hh.ru/applicant/negotiations")
            return True
        except Exception as e:
            logger.error(f"Ошибка навигации к откликам: {e}")
            return False

    async def close_modal(self) -> bool:
        """Закрывает модальное окно."""
        try:
            close_btn = self.page.locator('[data-qa="modal-close"]')
            if await close_btn.count() > 0:
                await close_btn.click()
                await self.anti_detect.random_delay()
                return True
            return False
        except Exception:
            return False

    async def go_back(self) -> bool:
        """Возврат на предыдущую страницу."""
        try:
            await self.page.go_back()
            await self.anti_detect.random_delay()
            return True
        except Exception:
            return False

    async def go_forward(self) -> bool:
        """Переход вперёд."""
        try:
            await self.page.go_forward()
            await self.anti_detect.random_delay()
            return True
        except Exception:
            return False
