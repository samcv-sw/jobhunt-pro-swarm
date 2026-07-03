# Milestone 1 Investigation & Architecture Plan: Initialize Expo App in `mobile/`

This report provides a complete, actionable, and copy-paste-ready blueprint for initializing the React Native Expo app in the `mobile/` directory, adhering strictly to the **AGENTS.md UI/UX guidelines** (Arabic/RTL, logical style properties, Cairo/Tajawal typography, cultural ergonomics) and integrating with the FastAPI backend in `web/frontend_api.py`.

---

## 1. Expo Initialization & Setup Command

To initialize a clean React Native Expo app in the `mobile/` directory using TypeScript and Expo Router (the modern standard for Expo navigation), execute the following commands from the workspace root directory:

```bash
# 1. Initialize Expo App with TypeScript template
npx create-expo-app@latest mobile --template blank-typescript

# 2. Navigate to the mobile directory
cd mobile

# 3. Install required Expo & core dependencies
npx expo install expo-font expo-localization expo-updates expo-router expo-status-bar react-native-safe-area-context react-native-screens

# 4. Install additional utility and icon libraries
npm install lucide-react-native
```

### Configuration: `app.json`
To support localized RTL text direction automatically upon device locale changes, add the `"locales"` and `"plugins"` support in `mobile/app.json`:

```json
{
  "expo": {
    "name": "JobHunt Pro",
    "slug": "jobhunt-pro-mobile",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "dark",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#121212"
    },
    "ios": {
      "supportsTablet": false,
      "bundleIdentifier": "com.jobhuntpro.mobile"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#121212"
      },
      "package": "com.jobhuntpro.mobile"
    },
    "plugins": [
      "expo-router"
    ],
    "extra": {
      "eas": {
        "projectId": "your-eas-project-id"
      }
    }
  }
}
```

---

## 2. Directory & File Structure

The recommended React Native Expo directory structure organizes source code cleanly, matching the Expo Router convention and keeping components modular and testable.

```
mobile/
├── app/                          # Expo Router Navigation Folder
│   ├── _layout.tsx               # Root Layout: font loading, provider, RTL check
│   ├── (auth)/                   # Authentication route group
│   │   ├── login.tsx             # Login Screen
│   │   └── register.tsx          # Fast Registration Screen
│   └── (tabs)/                   # Main tab navigation
│       ├── _layout.tsx           # Tab structure and styling
│       ├── index.tsx             # Dashboard Screen (Fetches stats, campaigns, jobs)
│       ├── campaigns.tsx         # Active Campaigns listing screen
│       └── jobs.tsx              # Matched / Applied Jobs list screen
├── assets/                       # Custom local assets
│   ├── fonts/                    # Local TTF/OTF fonts if Google Fonts is not used
│   └── images/                   # App logos and illustrations
├── src/                          # Application source code
│   ├── api/                      # Network requesting layer
│   │   └── client.ts             # API request wrapper with dynamic base URL
│   ├── components/               # Reusable custom UI components (AGENTS.md compliant)
│   │   ├── RTLText.tsx           # Customized Text component supporting Arabic & RTL
│   │   ├── RTLTextInput.tsx      # Customized TextInput component with auto-direction
│   │   ├── DirectionalIcon.tsx   # Auto-flipping Icon wrapper
│   │   └── ThemeButton.tsx       # Standard CTA buttons honoring Gulf ergonomics
│   ├── constants/                # Global configurations
│   │   └── theme.ts              # Cultural Colors & Styles
│   ├── hooks/                    # Reusable Hooks
│   │   └── useRTL.ts             # Fast RTL state helper
│   └── types/                    # TypeScript interfaces
│       └── index.ts              # API payload interfaces
├── app.json                      # Expo App Configuration
├── package.json                  # NPM dependencies
└── tsconfig.json                 # TypeScript rules
```

---

## 3. Implementing AGENTS.md Rules in React Native

React Native uses its own style engine (based on Yoga, implementing Flexbox). Below is the precise implementation of the **AGENTS.md** constraints in this mobile environment.

### A. RTL Layout & Toggling (`src/hooks/useRTL.ts`)
To toggle the language layout dynamically between Arabic (RTL) and English (LTR), React Native requires checking and setting `I18nManager`. 
Note that dynamic changes in `I18nManager` require a force reload using `expo-updates`.

```typescript
// src/hooks/useRTL.ts
import { I18nManager } from 'react-native';
import * as Updates from 'expo-updates';

export const useRTL = () => {
  const isRTL = I18nManager.isRTL;

  const setRTL = async (shouldBeRTL: boolean) => {
    if (isRTL !== shouldBeRTL) {
      I18nManager.allowRTL(shouldBeRTL);
      I18nManager.forceRTL(shouldBeRTL);
      
      // Reload is required for Yoga layout engine to flip coordinate system
      await Updates.reloadAsync();
    }
  };

  return {
    isRTL,
    textXDirection: isRTL ? -1 : 1,
    toggleRTL: () => setRTL(!isRTL),
    setRTL,
  };
};
```

### B. Logical Style Properties
In React Native, layout properties are already logical out-of-the-box when writing-direction aware variables are used:
* **Margin**: Use `marginStart` / `marginEnd` instead of `marginLeft` / `marginRight`.
* **Padding**: Use `paddingStart` / `paddingEnd` instead of `paddingLeft` / `paddingRight`.
* **Positioning**: Use `start` / `end` instead of `left` / `right`.
* **Borders**: Use `borderStartWidth` / `borderEndWidth` and `borderTopStartRadius` / `borderTopEndRadius`.
* **Flow Direction**: `flexDirection: 'row'` automatically acts as a row from right-to-left when RTL is active, avoiding manual coordination.

### C. Arabic Typography Component (`src/components/RTLText.tsx`)
This component enforces a **minimum font size of 14px** (recommends `16px`), **line-height ratio of 1.6 to 2.0**, **no letter spacing** for Arabic text, and default font-family to **Cairo** or **Tajawal**.

```typescript
// src/components/RTLText.tsx
import React from 'react';
import { Text, TextProps, StyleSheet, TextStyle, I18nManager } from 'react-native';

interface RTLTextProps extends TextProps {
  variant?: 'regular' | 'bold' | 'header';
  size?: number; // Desired size, will be restricted by min size rules
}

export const RTLText: React.FC<RTLTextProps> = ({
  children,
  style,
  variant = 'regular',
  size,
  ...props
}) => {
  // 1. Min font-size restriction (14px absolute min, recommend >= 16px)
  let fontSize = size || 16;
  if (fontSize < 14) {
    fontSize = 14;
  }

  // 2. Select appropriate font family
  let fontFamily = 'Cairo_Regular';
  if (variant === 'bold') {
    fontFamily = 'Cairo_Bold';
  } else if (variant === 'header') {
    fontFamily = 'Tajawal_Bold';
  }

  // 3. Line height multiplier (1.6 - 2.0)
  const lineHeight = fontSize * 1.6;

  const combinedStyles: TextStyle = {
    fontFamily,
    fontSize,
    lineHeight,
    letterSpacing: 0, // No letter-spacing on Arabic text
    color: '#E0E0E0',  // Light grey default for dark theme
    textAlign: I18nManager.isRTL ? 'right' : 'left',
  };

  return (
    <Text style={[combinedStyles, style]} {...props}>
      {children}
    </Text>
  );
};
```

### D. Auto-Direction Form Input (`src/components/RTLTextInput.tsx`)
Maps the CSS `dir="auto"` behavior. On iOS, we use `writingDirection: 'auto'`. On Android, we set the alignment dynamically based on standard characters.

```typescript
// src/components/RTLTextInput.tsx
import React, { useState } from 'react';
import { TextInput, TextInputProps, StyleSheet, I18nManager } from 'react-native';

export const RTLTextInput: React.FC<TextInputProps> = ({ style, value, onChangeText, ...props }) => {
  const [direction, setDirection] = useState<'ltr' | 'rtl'>('rtl');

  const handleTextChange = (text: string) => {
    // Detect first strong directional character (Arabic or Latin)
    const arabicRegex = /[\u0600-\u06FF]/;
    const latinRegex = /[a-zA-Z]/;
    
    if (arabicRegex.test(text)) {
      setDirection('rtl');
    } else if (latinRegex.test(text)) {
      setDirection('ltr');
    }
    
    if (onChangeText) {
      onChangeText(text);
    }
  };

  return (
    <TextInput
      style={[
        styles.input,
        {
          textAlign: direction === 'rtl' ? 'right' : 'left',
          writingDirection: 'auto', // iOS native auto direction support
        },
        style
      ]}
      value={value}
      onChangeText={handleTextChange}
      placeholderTextColor="#777"
      {...props}
    />
  );
};

const styles = StyleSheet.create({
  input: {
    fontFamily: 'Cairo_Regular',
    fontSize: 16,
    lineHeight: 24,
    color: '#FFFFFF',
    backgroundColor: '#1E1E1E',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#333333',
    minHeight: 48,
  },
});
```

### E. Directional Icons wrapper (`src/components/DirectionalIcon.tsx`)
Flips directional icons (like arrows and back buttons) when in RTL mode using a scaleX transform.

```typescript
// src/components/DirectionalIcon.tsx
import React from 'react';
import { View, ViewStyle, I18nManager } from 'react-native';

interface DirectionalIconProps {
  children: React.ReactNode;
  style?: ViewStyle;
}

export const DirectionalIcon: React.FC<DirectionalIconProps> = ({ children, style }) => {
  return (
    <View style={[{ transform: [{ scaleX: I18nManager.isRTL ? -1 : 1 }] }, style]}>
      {children}
    </View>
  );
};
```

### F. Cultural Ergonomics & Theme (`src/constants/theme.ts`)
Under the Gulf aesthetic context, the color schema is defined as:
* **Luxury Black/Gold**: Deep dark theme with rich gold highlight.
* **Trust Blue**: For system metrics and info states.
* **Success Green**: Safe verification and campaign runs.
* **Strict Error Red**: Destructive elements.
* **CTA Layout**: Centered or right-hand accessible floating action buttons.

```typescript
// src/constants/theme.ts
export const ThemeColors = {
  background: '#121212',      // Deep Luxury Black
  surface: '#1A1A1A',         // Soft Grey Card
  border: '#2C2C2C',          // Low-contrast separating lines
  
  // Gulf Region Signifiers
  gold: '#D4AF37',            // Luxury / Highlights
  goldHover: '#C5A880',       
  success: '#2E7D32',         // GCC Success Green
  trust: '#1E88E5',           // Gulf Corporate Blue
  error: '#D32F2F',           // Strict Warning Red
  
  // Typography
  textPrimary: '#FFFFFF',
  textSecondary: '#B0B0B0',
};

export const ThemeStyles = {
  ctaButton: {
    backgroundColor: ThemeColors.gold,
    borderRadius: 30,
    paddingVertical: 14,
    paddingHorizontal: 28,
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
    elevation: 6,
  },
};
```

---

## 4. Backend API Integration & Data Fetching

### HTTP Request Client (`src/api/client.ts`)
To fetch data from the FastAPI backend (e.g., `web/frontend_api.py`), the request client must handle emulator/simulator network routing differences for local development:
* **Android Emulator**: References local host as `10.0.2.2`.
* **iOS Simulator**: References local host as `localhost`.

```typescript
// src/api/client.ts
import { Platform } from 'react-native';

const getBaseUrl = (): string => {
  if (__DEV__) {
    // Maps localhost between Android Emulator and iOS Simulator correctly
    return Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';
  }
  return 'https://api.yourjobhuntapp.com'; // Production URL
};

export const BASE_URL = getBaseUrl();

export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options?.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.error || `Request failed with code ${response.status}`);
    }

    return (await response.json()) as T;
  } catch (error) {
    console.error(`API Fetch Error [${endpoint}]:`, error);
    throw error;
  }
}
```

---

## 5. Dashboard Screen Implementation (`app/(tabs)/index.tsx`)

This complete, production-ready screen implements the mobile dashboard. It:
1. Handles loading custom fonts on startup.
2. Checks state for a loaded `user_id` (simulates lookup from SQLite or context).
3. Fetches user stats, active campaigns, and matched jobs from the FastAPI endpoints in parallel.
4. Renders the layout using components designed to adhere to the Arabic/RTL typographic scale.

```typescript
// app/(tabs)/index.tsx
import React, { useState, useEffect } from 'react';
import { 
  StyleSheet, 
  View, 
  ScrollView, 
  TouchableOpacity, 
  ActivityIndicator, 
  RefreshControl,
  SafeAreaView
} from 'react-native';
import { RTLText } from '../../src/components/RTLText';
import { DirectionalIcon } from '../../src/components/DirectionalIcon';
import { apiFetch } from '../../src/api/client';
import { ThemeColors, ThemeStyles } from '../../src/constants/theme';
import { LucideBriefcase, LucideLayers, LucidePlay, LucideChevronRight, LucideCheckCircle } from 'lucide-react-native';

// API interfaces
interface UserStats {
  apps_sent: number;
  interviews: number;
  replies: number;
  match_rate: number;
  campaign?: { id: number; status: string } | null;
}

interface Job {
  id: number;
  title: string;
  company: string;
  source: string;
  score: number;
  status: string;
  sent_at?: string | null;
}

interface Campaign {
  id: number;
  campaign_id: string;
  name: string;
  status: string;
  apps_sent: number;
  total_attempted: number;
  open_count: number;
  response_count: number;
  jobs_found: number;
  created_at: string;
}

interface CampaignListResponse {
  campaigns: Campaign[];
  total: number;
}

interface JobsResponse {
  jobs: Job[];
  total: number;
}

export default function DashboardScreen() {
  const [userId, setUserId] = useState<string>('demo_user_123'); // Demo state, in production fetched from storage
  const [stats, setStats] = useState<UserStats | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [triggeringCampaign, setTriggeringCampaign] = useState<boolean>(false);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Perform parallel requests to FastAPI backend
      const [statsData, jobsData, campaignsData] = await Promise.all([
        apiFetch<UserStats>(`/api/user/stats?user_id=${userId}`),
        apiFetch<JobsResponse>(`/api/jobs/user?user_id=${userId}&limit=5`),
        apiFetch<CampaignListResponse>(`/api/campaign/list?user_id=${userId}`),
      ]);

      setStats(statsData);
      setJobs(jobsData.jobs || []);
      setCampaigns(campaignsData.campaigns || []);
    } catch (err) {
      console.error("Error loading dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const startNewCampaign = async () => {
    if (triggeringCampaign) return;
    try {
      setTriggeringCampaign(true);
      await apiFetch<{ ok: boolean; message: string }>(`/api/campaign/create`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId }),
      });
      // Refresh dashboard info
      await loadData();
    } catch (err) {
      console.error("Failed to initiate campaign", err);
    } finally {
      setTriggeringCampaign(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading && !refreshing) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={ThemeColors.gold} />
        <RTLText style={styles.loadingText}>جاري تحميل البيانات...</RTLText>
      </View>
    );
  }

  const activeCampaign = campaigns.find(c => c.status === 'active');

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView 
        contentContainerStyle={styles.container}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor={ThemeColors.gold} />
        }
      >
        {/* Welcome Header */}
        <View style={styles.header}>
          <View>
            <RTLText variant="header" size={24} style={styles.welcomeTitle}>أهلاً بك في لوحة التحكم</RTLText>
            <RTLText size={16} style={styles.subtitle}>شريكك الذكي في رحلتك الوظيفية</RTLText>
          </View>
        </View>

        {/* Stats Grid */}
        <View style={styles.statsGrid}>
          <View style={styles.statsCard}>
            <RTLText size={14} style={styles.statsLabel}>طلبات مرسلة</RTLText>
            <RTLText variant="bold" size={22} style={{ color: ThemeColors.trust }}>
              {stats?.apps_sent ?? 0}
            </RTLText>
          </View>
          <View style={styles.statsCard}>
            <RTLText size={14} style={styles.statsLabel}>معدل التطابق</RTLText>
            <RTLText variant="bold" size={22} style={{ color: ThemeColors.gold }}>
              {stats?.match_rate ?? 0}%
            </RTLText>
          </View>
          <View style={styles.statsCard}>
            <RTLText size={14} style={styles.statsLabel}>مقابلات نشطة</RTLText>
            <RTLText variant="bold" size={22} style={{ color: ThemeColors.success }}>
              {stats?.interviews ?? 0}
            </RTLText>
          </View>
          <View style={styles.statsCard}>
            <RTLText size={14} style={styles.statsLabel}>ردود الشركة</RTLText>
            <RTLText variant="bold" size={22} style={{ color: ThemeColors.textPrimary }}>
              {stats?.replies ?? 0}
            </RTLText>
          </View>
        </View>

        {/* Autopilot Campaign Banner */}
        <View style={styles.sectionHeader}>
          <RTLText variant="bold" size={18}>حملة الطيار الآلي</RTLText>
        </View>

        {activeCampaign ? (
          <View style={[styles.card, styles.campaignCardActive]}>
            <View style={styles.campaignHeader}>
              <View style={styles.row}>
                <LucideLayers size={20} color={ThemeColors.success} style={styles.iconMargin} />
                <RTLText variant="bold" size={16}>الحملة النشطة #{activeCampaign.id}</RTLText>
              </View>
              <View style={styles.badgeSuccess}>
                <RTLText size={12} style={styles.badgeText}>نشط</RTLText>
              </View>
            </View>
            <View style={styles.progressContainer}>
              <View style={styles.progressBarWrapper}>
                <View 
                  style={[
                    styles.progressBar, 
                    { width: `${Math.min(100, (activeCampaign.apps_sent / Math.max(1, activeCampaign.total_attempted)) * 100)}%` }
                  ]} 
                />
              </View>
              <View style={styles.progressLabels}>
                <RTLText size={14}>تم التقديم: {activeCampaign.apps_sent}</RTLText>
                <RTLText size={14}>الإجمالي: {activeCampaign.total_attempted}</RTLText>
              </View>
            </View>
          </View>
        ) : (
          <View style={styles.card}>
            <RTLText size={16} style={styles.campaignDesc}>
              لم تقم بتفعيل حملة تقديم تلقائي نشطة. ابدأ بتفعيل الطيار الآلي للتقديم على 200 وظيفة متوافقة مع سيرتك الذاتية.
            </RTLText>
            <TouchableOpacity 
              style={[ThemeStyles.ctaButton, styles.ctaAlign]} 
              onPress={startNewCampaign}
              disabled={triggeringCampaign}
            >
              {triggeringCampaign ? (
                <ActivityIndicator size="small" color="#000" />
              ) : (
                <View style={styles.row}>
                  <LucidePlay size={18} color="#000000" style={styles.iconMargin} />
                  <RTLText variant="bold" size={16} style={styles.ctaText}>تفعيل حملة جديدة</RTLText>
                </View>
              )}
            </TouchableOpacity>
          </View>
        )}

        {/* Jobs Section */}
        <View style={styles.sectionHeader}>
          <RTLText variant="bold" size={18}>الوظائف الأخيرة المطابقة</RTLText>
        </View>

        {jobs.length === 0 ? (
          <View style={styles.card}>
            <RTLText size={16} style={styles.emptyText}>لا توجد وظائف مطابقة متاحة حالياً.</RTLText>
          </View>
        ) : (
          jobs.map((job) => (
            <View key={job.id} style={styles.jobItem}>
              <View style={styles.row}>
                <LucideBriefcase size={20} color={ThemeColors.gold} style={styles.iconMargin} />
                <View style={styles.jobInfo}>
                  <RTLText variant="bold" size={16} numberOfLines={1}>{job.title}</RTLText>
                  <RTLText size={14} style={styles.jobCompany}>{job.company}</RTLText>
                </View>
              </View>
              <View style={styles.jobMeta}>
                <View style={styles.scoreBadge}>
                  <RTLText size={12} style={styles.scoreText}>مطابقة: {Math.round(job.score)}%</RTLText>
                </View>
                <DirectionalIcon>
                  <LucideChevronRight size={20} color={ThemeColors.textSecondary} />
                </DirectionalIcon>
              </View>
            </View>
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: ThemeColors.background,
  },
  container: {
    padding: 16,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: ThemeColors.background,
  },
  loadingText: {
    marginTop: 12,
    color: ThemeColors.textSecondary,
  },
  header: {
    marginBottom: 20,
    paddingVertical: 8,
  },
  welcomeTitle: {
    color: ThemeColors.textPrimary,
  },
  subtitle: {
    color: ThemeColors.textSecondary,
    marginTop: 4,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  statsCard: {
    width: '48%',
    backgroundColor: ThemeColors.surface,
    borderColor: ThemeColors.border,
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  statsLabel: {
    color: ThemeColors.textSecondary,
    marginBottom: 8,
  },
  sectionHeader: {
    marginBottom: 12,
    marginTop: 8,
    paddingHorizontal: 4,
  },
  card: {
    backgroundColor: ThemeColors.surface,
    borderColor: ThemeColors.border,
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  campaignCardActive: {
    borderColor: ThemeColors.success,
  },
  campaignHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  campaignDesc: {
    color: ThemeColors.textSecondary,
    marginBottom: 16,
  },
  ctaText: {
    color: '#000000',
  },
  ctaAlign: {
    alignSelf: 'stretch',
  },
  progressContainer: {
    marginTop: 8,
  },
  progressBarWrapper: {
    height: 8,
    backgroundColor: '#333',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressBar: {
    height: '100%',
    backgroundColor: ThemeColors.success,
  },
  progressLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  jobItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: ThemeColors.surface,
    borderColor: ThemeColors.border,
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  jobInfo: {
    flex: 1,
    marginStart: 12, // Logical Margin
  },
  jobCompany: {
    color: ThemeColors.textSecondary,
    marginTop: 2,
  },
  jobMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    marginStart: 8,
  },
  scoreBadge: {
    backgroundColor: '#2C2518',
    borderColor: ThemeColors.gold,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginEnd: 8, // Logical Margin
  },
  scoreText: {
    color: ThemeColors.gold,
  },
  badgeSuccess: {
    backgroundColor: '#1E3A20',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    color: ThemeColors.success,
  },
  emptyText: {
    color: ThemeColors.textSecondary,
    textAlign: 'center',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconMargin: {
    marginEnd: 8, // Logical Margin
  },
});
```

---

## 6. Root Layout Setup (`app/_layout.tsx`)

This structure loads the required custom Google Fonts and holds them on the screen until they are fully available.

```typescript
// app/_layout.tsx
import React, { useEffect } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { Slot, SplashScreen } from 'expo-router';
import { useFonts, Cairo_400Regular, Cairo_700Bold } from '@expo-google-fonts/cairo';
import { Tajawal_400Regular, Tajawal_700Bold } from '@expo-google-fonts/tajawal';
import { StatusBar } from 'expo-status-bar';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Cairo_Regular: Cairo_400Regular,
    Cairo_Bold: Cairo_700Bold,
    Tajawal_Regular: Tajawal_400Regular,
    Tajawal_Bold: Tajawal_700Bold,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded, fontError]);

  if (!fontsLoaded && !fontError) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#D4AF37" />
      </View>
    );
  }

  return (
    <>
      <StatusBar style="light" />
      <Slot />
    </>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#121212',
  },
});
```

---

## Summary of Findings & Next Steps
1. The backend exposes standard REST endpoints built for dynamic SQLite integration. These can be fetched over JSON payloads from the React Native app.
2. Expo native components automatically adjust layout structures based on `I18nManager.isRTL` settings. Standard React Native properties (`paddingStart`, `marginStart`) perfectly map CSS Logical Properties.
3. Loading Google Fonts via `expo-font` ensures typography matches the local regional layout rules, satisfying typography mandates for size and line height.
