# Analysis Report — React Native Expo Mobile App Implementation Plan

## Executive Summary
This report outlines the technical strategy, commands, and implementation patterns to build a clean, production-ready React Native Expo mobile application in the `mobile/` directory. It incorporates local-first developer setup parameters to connect to the FastAPI backend and provides complete, copy-paste-ready React Native patterns that strictly enforce the **RTL layout, logical properties, and Arabic typography** guidelines defined in `AGENTS.md`.

---

## 1. Expo App Initialization

### Command to Initialize
To initialize a clean, modern React Native Expo app with TypeScript in the `mobile/` directory, use the official Expo CLI template:

```bash
npx create-expo-app@latest mobile --template blank-typescript
```

### Installation of Recommended Dependencies
Run these commands within the `mobile/` directory to install custom fonts, translation helpers, storage, and networking packages:

```bash
cd mobile
# Install Expo Fonts and Google Fonts
npx expo install expo-font @expo-google-fonts/cairo @expo-google-fonts/tajawal

# Install Local Storage for storing user session (user_id)
npx expo install @react-native-async-storage/async-storage

# Install Localization plugin (to support device locale checking)
npx expo install expo-localization

# Install Vector Icons (pre-installed, but ensure updated)
npx expo install @expo/vector-icons
```

### Configuration: Enabling Native RTL in `app.json`
To allow the native Android and iOS runners to render RTL layouts correctly, the `"supportsRTL": true` configuration must be added to `app.json`. Modify the generated `app.json` to match:

```json
{
  "expo": {
    "name": "JobHunt Pro Mobile",
    "slug": "jobhunt-pro-mobile",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "light",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "ios": {
      "supportsTablet": true,
      "supportsRTL": true
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "supportsRTL": true
    },
    "extra": {
      "supportsRTL": true
    },
    "plugins": [
      "expo-localization"
    ]
  }
}
```

---

## 2. Directory Structure
A modular structure is used. It supports file-based routing via `expo-router` or traditional navigation. Below is the proposed layout using a standard `src/` modular layout:

```text
mobile/
├── assets/                    # App icons, splash screens, static local files
├── src/
│   ├── components/            # Reusable UI components
│   │   ├── CustomText.tsx     # Typography enforcing AGENTS.md rules
│   │   ├── DirectionalIcon.tsx# Icon scaling wrapper for RTL
│   │   └── MetricCard.tsx     # Reusable dashboard stats card
│   ├── constants/
│   │   └── Colors.ts          # Color tokens (success-green, trust-blue, error-red, luxury-black/gold)
│   ├── hooks/
│   │   └── useAuth.ts         # User session and ID retrieval/caching
│   ├── navigation/
│   │   └── AppNavigator.tsx   # Stack & Tab Navigator definition
│   ├── screens/
│   │   ├── LoginScreen.tsx    # Passwordless lookup by email
│   │   └── DashboardScreen.tsx# Core dashboard with stats, campaign controls, and matched jobs
│   └── services/
│       └── api.ts             # API client targeting FastAPI endpoints
├── app.json                   # Expo application config
├── App.tsx                    # Root entry point, handles custom font pre-loading
├── package.json               # NPM packages and scripts
└── tsconfig.json              # TypeScript compilation rules
```

---

## 3. Implementing AGENTS.md Rules in React Native

The styling guidelines of `AGENTS.md` can be fully achieved in React Native. Since React Native relies on the **Yoga Layout Engine**, we translate web-based CSS directives into React Native style attributes.

### Rule 3.1: Logical Layout Properties
In React Native, physical styling (`left`, `right`, `marginLeft`, `paddingRight`) is replaced by logical styling. The Yoga engine automatically mirrors start/end configurations when the layout direction changes:

*   **Margin**: Replace `marginLeft` and `marginRight` with `marginStart` and `marginEnd`.
*   **Padding**: Replace `paddingLeft` and `paddingRight` with `paddingStart` and `paddingEnd`.
*   **Absolute positioning**: Replace `left` and `right` with `start` and `end`.
*   **Borders**: Replace `borderTopLeftRadius` and `borderTopRightRadius` with `borderTopStartRadius` and `borderTopEndRadius`.

*Example of a logical flex layout in React Native:*
```typescript
const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',        // In RTL, items render from right to left automatically
    alignItems: 'center',
    paddingStart: 16,            // Logical start padding
    paddingEnd: 24,              // Logical end padding
    marginTop: 12,
  },
  card: {
    marginStart: 8,             // Space at the logical start edge of the component
    borderTopStartRadius: 12,    // Rounded corner on top-left (LTR) or top-right (RTL)
  }
});
```

### Rule 3.2: RTL Toggle and App Startup Setup
We import `I18nManager` from `'react-native'` to force RTL rendering.
To apply change during development or runtime, we call `I18nManager.forceRTL(true)` and restart the application:

```typescript
import { I18nManager } from 'react-native';

export function initializeLayoutDirection(isRTL: boolean) {
  try {
    I18nManager.allowRTL(isRTL);
    I18nManager.forceRTL(isRTL);
  } catch (error) {
    console.warn("Failed to set layout direction: ", error);
  }
}
```

### Rule 3.3: Arabic Typography (Cairo & Tajawal)
To meet the constraints:
1.  **Min Font Size**: Prevent fonts from rendering smaller than `14px` (recommend `>= 16px` for readability).
2.  **Line Height**: Set to `1.6` to `2.0` times the font size. In React Native, `lineHeight` must be defined as an absolute number (not a unitless scale).
3.  **No Letter Spacing**: Set `letterSpacing: 0` explicitly.

Below is a complete, copy-paste-ready wrapper `<CustomText>` component implementing these constraints:

```typescript
// src/components/CustomText.tsx
import React from 'react';
import { Text, TextProps, StyleSheet, I18nManager } from 'react-native';
import { COLORS } from '../constants/Colors';

interface CustomTextProps extends TextProps {
  variant?: 'regular' | 'bold' | 'header';
  size?: number; // Minimum enforced size: 14px, default: 16px
}

export function CustomText({ variant = 'regular', size = 16, style, children, ...props }: CustomTextProps) {
  const fontStyle = styles[variant];
  const fontSize = size < 14 ? 14 : size; // Enforces minimum font size constraint
  const lineHeight = Math.round(fontSize * 1.75); // Calculates line-height between 1.6x and 2.0x

  return (
    <Text
      style={[
        styles.baseText,
        fontStyle,
        { fontSize, lineHeight },
        style
      ]}
      {...props}
    >
      {children}
    </Text>
  );
}

const styles = StyleSheet.create({
  baseText: {
    color: COLORS.textPrimary,
    textAlign: I18nManager.isRTL ? 'right' : 'left',
    writingDirection: I18nManager.isRTL ? 'rtl' : 'ltr',
    letterSpacing: 0, // Explicitly no letter-spacing to prevent breaking Arabic connections
  },
  regular: {
    fontFamily: 'Cairo-Regular',
  },
  bold: {
    fontFamily: 'Cairo-Bold',
  },
  header: {
    fontFamily: 'Tajawal-Bold',
  },
});
```

### Rule 3.4: Directional Icon Flipping
React Native vector icons do not mirror automatically. We must apply a transform to scale the X-axis by `-1` when in RTL mode:

```typescript
// src/components/DirectionalIcon.tsx
import React from 'react';
import { View, StyleProp, ViewStyle, I18nManager } from 'react-native';

interface DirectionalIconProps {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

export function DirectionalIcon({ children, style }: DirectionalIconProps) {
  const isRTL = I18nManager.isRTL;
  return (
    <View style={[{ transform: [{ scaleX: isRTL ? -1 : 1 }] }, style]}>
      {children}
    </View>
  );
}
```

### Rule 3.5: Color Tokens and Cultural Ergonomics
*   **Color Palette**: Define in `src/constants/Colors.ts`:
    ```typescript
    export const COLORS = {
      primary: '#1D4ED8',      // Trust blue
      success: '#10B981',      // Success green
      error: '#EF4444',        // Strict error red
      luxuryBlack: '#111827',  // Luxury black
      luxuryGold: '#D97706',   // Luxury gold
      background: '#F3F4F6',   // Neutral light gray
      cardBg: '#FFFFFF',
      textPrimary: '#1F2937',
      textSecondary: '#6B7280',
      border: '#E5E7EB',
    };
    ```
*   **Cultural Ergonomics (CTAs)**: Primary buttons are kept centrally located or positioned within easy reach of right-handed mobile thumbs (bottom-center or bottom-right). This avoids placing crucial action buttons in hard-to-reach locations due to mechanical left-mirroring.

---

## 4. Backend API Fetching and Networking Setup

The backend servers run on `localhost`. However, a mobile device/emulator cannot access `localhost` directly. We must configure the api handler to support emulator IP mapping:

*   **iOS Simulator**: Reaches host system via `http://localhost:8000`.
*   **Android Emulator**: Reaches host system via loopback bridge IP `http://10.0.2.2:8000`.
*   **Physical Testing Device**: Must connect to the local IP of the host machine (e.g. `http://192.168.1.50:8000`) or via an active Ngrok tunnel.

### Complete, Copy-Paste API Service (`src/services/api.ts`)

```typescript
// src/services/api.ts
import { Platform } from 'react-native';

const DEV_API_URL = Platform.select({
  ios: 'http://localhost:8000',
  android: 'http://10.0.2.2:8000',
  default: 'http://localhost:8000',
});

// Configure EXPO_PUBLIC_API_URL in a .env file at the root of mobile/
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || DEV_API_URL;

export interface FetchOptions extends RequestInit {
  params?: Record<string, string>;
}

async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { params, headers, ...rest } = options;
  
  let url = `${API_BASE_URL}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams(params);
    url += `?${searchParams.toString()}`;
  }

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    ...rest,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Server returned error status: ${response.status}`);
  }

  return response.json();
}

// Data Interface Contracts Matching the FastAPI schemas
export interface UserProfile {
  id: number;
  user_id: string;
  email: string;
  name: string;
  phone: string;
  target_roles: string;
  target_locations: string;
  min_salary: number;
  balance: number;
  created_at: string;
  is_active: boolean;
}

export interface UserStats {
  apps_sent: number;
  interviews: number;
  replies: number;
  match_rate: number;
  campaign: { id: number; status: string } | null;
}

export interface Campaign {
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

export interface Job {
  id: number;
  title: string;
  company: string;
  source: string;
  score: number;
  status: string;
  sent_at?: string;
}

export const api = {
  getUserByEmail: (email: string) => 
    apiFetch<UserProfile>('/api/user/by-email', { params: { email } }),

  getUserStats: (userId: string) => 
    apiFetch<UserStats>('/api/user/stats', { params: { user_id: userId } }),

  getCampaigns: (userId: string) => 
    apiFetch<{ campaigns: Campaign[]; total: number }>('/api/campaign/list', { params: { user_id: userId } }),

  createCampaign: (userId: string) => 
    apiFetch<{ ok: boolean; campaign_id: string; message: string }>('/api/campaign/create', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    }),

  getUserJobs: (userId: string, limit = 20) => 
    apiFetch<{ jobs: Job[]; total: number }>('/api/jobs/user', { params: { user_id: userId, limit: String(limit) } }),
};
```

---

## 5. Complete, Copy-Paste Dashboard Screen (`src/screens/DashboardScreen.tsx`)

This dashboard connects directly to the API, handles RTL layouts elegantly, uses the custom logical typography components, and places controls in ergonomic, thumb-reachable locations.

```typescript
// src/screens/DashboardScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  I18nManager,
  SafeAreaView,
  Alert
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

import { api, UserStats, Job } from '../services/api';
import { COLORS } from '../constants/Colors';
import { CustomText } from '../components/CustomText';
import { DirectionalIcon } from '../components/DirectionalIcon';

export function DashboardScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [userId, setUserId] = useState<string>('');

  useEffect(() => {
    loadUserSession();
  }, []);

  const loadUserSession = async () => {
    try {
      const storedUid = await AsyncStorage.getItem('user_id');
      if (storedUid) {
        setUserId(storedUid);
        await fetchData(storedUid);
      } else {
        // Fallback for testing: assume a standard test user_id or redirect to login
        const fallbackUid = 'dev_test_user';
        setUserId(fallbackUid);
        await fetchData(fallbackUid);
      }
    } catch (e) {
      Alert.alert('Session Error', 'Could not read user configuration.');
    } finally {
      setLoading(false);
    }
  };

  const fetchData = async (uid: string) => {
    try {
      const [statsData, jobsData] = await Promise.all([
        api.getUserStats(uid),
        api.getUserJobs(uid, 10),
      ]);
      setStats(statsData);
      setJobs(jobsData.jobs);
    } catch (error) {
      console.error('Fetch error:', error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData(userId);
    setRefreshing(false);
  };

  const handleStartCampaign = async () => {
    try {
      setLoading(true);
      const res = await api.createCampaign(userId);
      Alert.alert('الطيار الآلي', res.message);
      await fetchData(userId);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to initialize campaign.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !refreshing) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  const isCampaignActive = stats?.campaign?.status === 'active';

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        {/* Arabic Header */}
        <View style={styles.header}>
          <CustomText variant="header" size={24} style={styles.headerTitle}>
            لوحة التحكم
          </CustomText>
          <TouchableOpacity onPress={handleRefresh} style={styles.iconButton}>
            <DirectionalIcon>
              <Ionicons name="refresh" size={24} color={COLORS.luxuryBlack} />
            </DirectionalIcon>
          </TouchableOpacity>
        </View>

        {/* Stats Grid using Logical Flexbox */}
        <View style={styles.statsGrid}>
          <View style={styles.statsRow}>
            <View style={styles.metricCard}>
              <CustomText variant="bold" size={20}>{stats?.apps_sent ?? 0}</CustomText>
              <CustomText variant="regular" size={14} style={styles.metricLabel}>
                طلبات مرسلة
              </CustomText>
            </View>
            <View style={styles.metricCard}>
              <CustomText variant="bold" size={20} style={{ color: COLORS.success }}>
                {stats?.interviews ?? 0}
              </CustomText>
              <CustomText variant="regular" size={14} style={styles.metricLabel}>
                مقابلات مجدولة
              </CustomText>
            </View>
          </View>

          <View style={styles.statsRow}>
            <View style={styles.metricCard}>
              <CustomText variant="bold" size={20}>{stats?.replies ?? 0}</CustomText>
              <CustomText variant="regular" size={14} style={styles.metricLabel}>
                الردود المستلمة
              </CustomText>
            </View>
            <View style={styles.metricCard}>
              <CustomText variant="bold" size={20} style={{ color: COLORS.primary }}>
                {stats?.match_rate ?? 0}%
              </CustomText>
              <CustomText variant="regular" size={14} style={styles.metricLabel}>
                نسبة التطابق
              </CustomText>
            </View>
          </View>
        </View>

        {/* Autopilot Campaign Section */}
        <View style={styles.campaignContainer}>
          <CustomText variant="bold" size={18} style={styles.sectionTitle}>
            حملة التوظيف الآلية
          </CustomText>
          
          <View style={styles.campaignStatusCard}>
            <View style={styles.statusHeader}>
              <CustomText variant="regular" size={16}>حالة الحملة:</CustomText>
              <View style={[
                styles.badge, 
                { backgroundColor: isCampaignActive ? COLORS.success + '20' : '#E5E7EB' }
              ]}>
                <CustomText variant="bold" size={14} style={{ color: isCampaignActive ? COLORS.success : COLORS.textSecondary }}>
                  {isCampaignActive ? 'نشطة' : 'متوقفة'}
                </CustomText>
              </View>
            </View>

            {/* Ergonomically Placed Action Button (Centred for easy reach) */}
            {!isCampaignActive && (
              <TouchableOpacity style={styles.ctaButton} onPress={handleStartCampaign}>
                <CustomText variant="bold" size={16} style={styles.ctaButtonText}>
                  بدء حملة الطيار الآلي
                </CustomText>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Jobs List Section */}
        <View style={styles.jobsSection}>
          <CustomText variant="bold" size={18} style={styles.sectionTitle}>
            أحدث الوظائف المتطابقة
          </CustomText>

          {jobs.length === 0 ? (
            <View style={styles.emptyContainer}>
              <CustomText variant="regular" size={14} style={{ color: COLORS.textSecondary }}>
                لا توجد وظائف متطابقة حالياً.
              </CustomText>
            </View>
          ) : (
            jobs.map((job) => (
              <View key={job.id} style={styles.jobCard}>
                <View style={styles.jobHeader}>
                  <CustomText variant="bold" size={16} style={styles.jobTitle}>
                    {job.title}
                  </CustomText>
                  <View style={[styles.badge, { backgroundColor: COLORS.primary + '15' }]}>
                    <CustomText variant="bold" size={12} style={{ color: COLORS.primary }}>
                      {Math.round(job.score)}%
                    </CustomText>
                  </View>
                </View>
                
                <View style={styles.jobFooter}>
                  <CustomText variant="regular" size={14} style={{ color: COLORS.textSecondary }}>
                    {job.company}
                  </CustomText>
                  <View style={[
                    styles.statusBadge,
                    { backgroundColor: job.status === 'applications' ? COLORS.success + '15' : '#F3F4F6' }
                  ]}>
                    <CustomText variant="regular" size={12} style={{ color: job.status === 'applications' ? COLORS.success : COLORS.textSecondary }}>
                      {job.status === 'applications' ? 'تم التقديم' : 'متطابقة'}
                    </CustomText>
                  </View>
                </View>
              </View>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContainer: {
    padding: 16,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    marginTop: 8,
  },
  headerTitle: {
    color: COLORS.luxuryBlack,
  },
  iconButton: {
    padding: 8,
    backgroundColor: COLORS.cardBg,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  sectionTitle: {
    marginBottom: 12,
    marginTop: 8,
    color: COLORS.luxuryBlack,
  },
  statsGrid: {
    marginBottom: 20,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  metricCard: {
    flex: 1,
    backgroundColor: COLORS.cardBg,
    borderRadius: 12,
    padding: 16,
    marginEnd: 6,
    marginStart: 6,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  metricLabel: {
    color: COLORS.textSecondary,
    marginTop: 4,
  },
  campaignContainer: {
    marginBottom: 20,
  },
  campaignStatusCard: {
    backgroundColor: COLORS.cardBg,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  badge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 16,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  ctaButton: {
    backgroundColor: COLORS.luxuryBlack,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: COLORS.luxuryGold, // Gold border adds luxury look
  },
  ctaButtonText: {
    color: '#FFFFFF',
  },
  jobsSection: {
    marginBottom: 24,
  },
  emptyContainer: {
    backgroundColor: COLORS.cardBg,
    padding: 24,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  jobCard: {
    backgroundColor: COLORS.cardBg,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  jobHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  jobTitle: {
    flex: 1,
    paddingEnd: 12, // Ensure text does not overlap with badge
  },
  jobFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
});
```

---

## 6. App Bootstrapping Entry Point (`App.tsx`)

This acts as the root entry point which registers the forced RTL layouts, loads the Cairo and Tajawal fonts asynchronously, and displays a splash screen/loading indicator until assets are resolved.

```typescript
// App.tsx
import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, StyleSheet, I18nManager } from 'react-native';
import { useFonts } from 'expo-font';
import { Cairo_400Regular, Cairo_700Bold } from '@expo-google-fonts/cairo';
import { Tajawal_400Regular, Tajawal_700Bold } from '@expo-google-fonts/tajawal';

import { DashboardScreen } from './src/screens/DashboardScreen';
import { COLORS } from './src/constants/Colors';

export default function App() {
  const [rtlInitialized, setRtlInitialized] = useState(false);

  // Load custom typography as required by AGENTS.md
  const [fontsLoaded] = useFonts({
    'Cairo-Regular': Cairo_400Regular,
    'Cairo-Bold': Cairo_700Bold,
    'Tajawal-Regular': Tajawal_400Regular,
    'Tajawal-Bold': Tajawal_700Bold,
  });

  useEffect(() => {
    // Force RTL direction for Arabic interface
    const initializeRTL = async () => {
      try {
        if (!I18nManager.isRTL) {
          I18nManager.allowRTL(true);
          I18nManager.forceRTL(true);
          // Note: In a production native build, calling forceRTL triggers an asynchronous app reload.
        }
      } catch (error) {
        console.warn('RTL initialization error:', error);
      } finally {
        setRtlInitialized(true);
      }
    };

    initializeRTL();
  }, []);

  if (!fontsLoaded || !rtlInitialized) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  // Once fonts are loaded and RTL layout is forced, bootstrap the main dashboard
  return <DashboardScreen />;
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
});
```

---

## Conclusion & Actionable Steps
1.  **Initialize the codebase**: Run `npx create-expo-app@latest mobile --template blank-typescript`.
2.  **Add Configuration**: Insert `"supportsRTL": true` to the iOS, Android, and Extra fields in `app.json`.
3.  **Install Font packages**: Add Cairo and Tajawal packages.
4.  **Copy-paste Base Modules**: Drop the `src/components/CustomText.tsx`, `src/services/api.ts`, and `src/screens/DashboardScreen.tsx` files directly into their respective slots.
5.  **Run locally**: Execute `npx expo start` to launch development servers.
