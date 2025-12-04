import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import da from './locales/da.json'
import es from './locales/es.json'
import pt from './locales/pt.json'
import no from './locales/no.json'
import sv from './locales/sv.json'
import de from './locales/de.json'

export type Locale = 'en' | 'da' | 'es' | 'pt' | 'no' | 'sv' | 'de'

export const LOCALES: { code: Locale; name: string; flag: string }[] = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'da', name: 'Dansk', flag: '🇩🇰' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'no', name: 'Norsk', flag: '🇳🇴' },
  { code: 'sv', name: 'Svenska', flag: '🇸🇪' },
]

// Get saved locale or detect from browser
function getDefaultLocale(): Locale {
  const saved = localStorage.getItem('locale') as Locale | null
  if (saved && LOCALES.some(l => l.code === saved)) {
    return saved
  }

  // Try to detect from browser
  const browserLang = navigator.language.split('-')[0]
  const matched = LOCALES.find(l => l.code === browserLang)
  return matched ? matched.code : 'en'
}

const i18n = createI18n({
  legacy: false,
  locale: getDefaultLocale(),
  fallbackLocale: 'en',
  messages: {
    en,
    da,
    es,
    pt,
    no,
    sv,
    de
  }
})

export function setLocale(locale: Locale) {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  document.documentElement.lang = locale
}

export default i18n
