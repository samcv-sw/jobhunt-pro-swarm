"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import arTranslations from "../locales/ar.json";
import enTranslations from "../locales/en.json";

export type Locale = "ar" | "en";

interface LocaleContextType {
  locale: Locale;
  isArabic: boolean;
  setLocale: (locale: Locale) => void;
  toggleLocale: () => void;
  t: (key: string, variables?: Record<string, string | number>) => string;
}

const LocaleContext = createContext<LocaleContextType | undefined>(undefined);

const translations: Record<Locale, any> = {
  ar: arTranslations,
  en: enTranslations,
};

interface LocaleProviderProps {
  children: React.ReactNode;
  initialLocale?: Locale;
}

export function LocaleProvider({ children, initialLocale = "ar" }: LocaleProviderProps) {
  const [locale, setLocaleState] = useState<Locale>(initialLocale);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    if (typeof document !== "undefined") {
      document.cookie = `locale=${newLocale}; path=/; max-age=31536000; SameSite=Lax`;
    }
  };

  const toggleLocale = () => {
    const nextLocale = locale === "ar" ? "en" : "ar";
    setLocale(nextLocale);
  };

  const isArabic = locale === "ar";

  const t = (key: string, variables?: Record<string, string | number>): string => {
    const keys = key.split(".");
    let val: any = translations[locale];
    for (const k of keys) {
      if (val && typeof val === "object" && k in val) {
        val = val[k];
      } else {
        return key;
      }
    }
    if (typeof val !== "string") {
      return key;
    }
    if (variables) {
      let result = val;
      for (const [vKey, vVal] of Object.entries(variables)) {
        result = result.replace(new RegExp(`{${vKey}}`, "g"), String(vVal));
      }
      return result;
    }
    return val;
  };

  useEffect(() => {
    if (typeof document !== "undefined" && document.documentElement) {
      document.documentElement.lang = locale;
      document.documentElement.dir = locale === "ar" ? "rtl" : "ltr";
    }
  }, [locale]);

  return (
    <LocaleContext.Provider value={{ locale, isArabic, setLocale, toggleLocale, t }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error("useLocale must be used within a LocaleProvider");
  }
  return context;
}

