# Milestone 3 Investigation & Recommendation Report: Initialize Expo App in `mobile/`

This report provides recommendations and execution plans for Milestone 1 of Milestone 3: initializing a clean React Native Expo app in the `mobile/` directory, conforming to `AGENTS.md` RTL/Arabic styling rules, and connecting to the FastAPI backend.

---

## 1. Command to Initialize a Clean React Native Expo App
To initialize a clean React Native Expo app using TypeScript and Expo Router (the current industry standard for SDK 50+), execute the following commands in the workspace root:

```bash
# Navigate to the workspace and initialize the Expo app in the mobile/ directory
npx create-expo-app@latest mobile --template blank-typescript
```

This creates a clean, lightweight React Native workspace under `mobile/` using TypeScript, avoiding bloated pre-configured templates, and allowing us to build the structure clean.

### Essential Packages to Install Next
Once initialized, navigate to the `mobile/` directory and install the necessary dependencies for navigation, styling, icons, and fonts:

```bash
cd mobile

# Expo Router & Navigation dependencies
npx expo install expo-router react-native-safe-area-context react-native-screens expo-linking expo-constants expo-status-bar

# Google Fonts (Cairo & Tajawal) support
npx expo install expo-font @expo-google-fonts/cairo @expo-google-fonts/tajawal

# Localization & RTL utilities
npx expo install expo-localization

# Icon support (using Expo Vector Icons which is pre-installed, or installing lucide-react-native)
npm install lucide-react-native
```

---

## 2. Directory Layout & App Structure
The recommended directory layout utilizes the file-based Expo Router. It separates screens, layout, reusable styling wrappers, and data-fetching hooks.

```
mobile/
├── app/                           # Expo Router App Directory
│   ├── (tabs)/                    # Tab Navigation Group
│   │   ├── _layout.tsx            # Tab Bar Navigation configuration
│   │   ├── index.tsx              # Dashboard Screen (Overview & Stats)
│   │   ├── campaigns.tsx          # Campaigns Management Screen
│   │   └── jobs.tsx               # Matched/Applied Jobs Screen
│   ├── _layout.tsx                # Root App Layout (Loads fonts & handles RTL initialization)
│   └── login.tsx                  # Login / Session Initialization Screen
├── assets/
│   └── fonts/                     # Local fallback font files if needed
├── components/                    # Core UI components enforcing AGENTS.md rules
│   ├── ArabicText.tsx             # Typographic wrapper for Cairo/Tajawal
│   ├── ArabicTextInput.tsx        # TextInput component enforcing auto writing direction
│   ├── Container.tsx              # Root Screen Wrapper applying logical layout constraints
│   └── RTLIcon.tsx                # Icon wrapper applying scaleX mirroring under RTL
├── hooks/
│   └── useApi.ts                  # Custom hook for backend endpoints
├── constants/
│   └── Colors.ts                  # Gulf-region cultural color scheme (Black/Gold/Green/Blue)
├── app.json                       # Expo configuration (contains RTL plugins config)
├── package.json                   # Dependencies & Start scripts
└── tsconfig.json                  # TypeScript compiler settings
```

---

## 3. Implementing AGENTS.md Rules in React Native
React Native does not use standard CSS stylesheets, but the layout engine (Yoga) translates layout properties. Below is how we map the rules from `AGENTS.md` to React Native.

### A. Layout direction & CSS Logical Properties Mapping
In React Native, we replace physical layout properties (`left`/`right`, `paddingLeft`/`paddingRight`) with logical layout properties which automatically mirror based on the layout direction (`I18nManager.isRTL`).

| Web CSS Property | React Native Style Equivalent | Description |
| :--- | :--- | :--- |
| `margin-left` | `marginStart` | Margin at the start of the layout flow |
| `margin-right` | `marginEnd` | Margin at the end of the layout flow |
| `padding-left` | `paddingStart` | Padding at the start of the layout flow |
| `padding-right` | `paddingEnd` | Padding at the end of the layout flow |
| `left` | `start` | Positional offset from start boundary |
| `right` | `end` | Positional offset from end boundary |
| `border-left-width` | `borderStartWidth` | Left border width maps to start border width |
| `border-right-width` | `borderEndWidth` | Right border width maps to end border width |
| `inline-size` | *Use flexbox properties or `width: "100%"`* | Explicit `inline-size` is not supported; use standard Flexbox layouts |
| `block-size` | *Use flexbox properties or `height`* | Explicit `block-size` is not supported; use standard Flexbox layouts |

### B. Typography & Font Configuration
1. **Fonts**: Load and use `'Cairo'` and `'Tajawal'`.
2. **Font Size**: Minimum of `14px` (recommended `16px` for primary body text).
3. **Line Height**: React Native requires `lineHeight` to be a absolute number (`fontSize * multiplier`), not a unitless scale multiplier. We enforce `lineHeight: fontSize * 1.6` to `2.0`.
4. **No letter spacing**: Explicitly omit `letterSpacing` or set it to `0` for Arabic text.

### C. Directional Icons
We mirror icons based on RTL using a scale factor:
- LTR scale: `1`
- RTL scale: `-1`
We implement this via `transform: [{ scaleX: I18nManager.isRTL ? -1 : 1 }]`.

### Reusable UI Wrapper Components

Below are the complete, copy-paste-ready implementations of components that enforce these guidelines.

#### Root Layout Configuration: `mobile/app/_layout.tsx`
Handles loading custom fonts and ensuring the system RTL configuration is initialized.
```typescript
import React, { useEffect } from 'react';
import { SplashScreen, Stack } from 'expo-router';
import { useFonts, Cairo_400Regular, Cairo_700Bold } from '@expo-google-fonts/cairo';
import { Tajawal_400Regular, Tajawal_700Bold } from '@expo-google-fonts/tajawal';
import { I18nManager, ActivityIndicator, View } from 'react-native';

// Force RTL layout support if necessary
I18nManager.allowRTL(true);
// Example: Force RTL layout for testing or based on Arabic locales
// I18nManager.forceRTL(true); 

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    'Cairo-Regular': Cairo_400Regular,
    'Cairo-Bold': Cairo_700Bold,
    'Tajawal-Regular': Tajawal_400Regular,
    'Tajawal-Bold': Tajawal_700Bold,
  });

  useEffect(() => {
    if (fontsLoaded) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded]);

  if (!fontsLoaded) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#111827' }}>
        <ActivityIndicator size="large" color="#D4AF37" />
      </View>
    );
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(tabs)" />
      <Stack.Screen name="login" />
    </Stack>
  );
}
```

#### Reusable Text Wrapper: `mobile/components/ArabicText.tsx`
Enforces the custom fonts, line height, letter spacing constraint, and minimum size recommendations.
```typescript
import React from 'react';
import { Text as RNText, TextStyle, TextProps } from 'react-native';

interface ArabicTextProps extends TextProps {
  style?: TextStyle | TextStyle[];
  variant?: 'body' | 'title' | 'bold' | 'caption';
  fontSize?: number;
}

export const ArabicText: React.FC<ArabicTextProps> = ({
  children,
  style,
  variant = 'body',
  fontSize: customFontSize,
  ...props
}) => {
  // Determine standard font sizes based on variant
  let size = customFontSize || 16;
  let fontFamily = 'Cairo-Regular';

  if (variant === 'title') {
    size = customFontSize || 22;
    fontFamily = 'Cairo-Bold';
  } else if (variant === 'bold') {
    size = customFontSize || 16;
    fontFamily = 'Cairo-Bold';
  } else if (variant === 'caption') {
    size = customFontSize || 14; // absolute minimum permitted limit
    fontFamily = 'Tajawal-Regular';
  }

  // AGENTS.md: Line height should be 1.6 to 2.0
  const lineHeight = size * 1.6;

  const combinedStyles: TextStyle = {
    fontFamily,
    fontSize: size,
    lineHeight,
    letterSpacing: 0, // Enforce no letter spacing for Arabic legibility
    textAlign: 'right', // Default to right text align for Arabic RTL
    color: '#E5E7EB', // Default light text color on dark themes
    ...(Array.isArray(style) ? Object.assign({}, ...style) : style),
  };

  return (
    <RNText style={combinedStyles} {...props}>
      {children}
    </RNText>
  );
};
```

#### Reusable TextInput: `mobile/components/ArabicTextInput.tsx`
Enforces input direction auto-detection.
```typescript
import React from 'react';
import { TextInput as RNTextInput, TextInputProps, StyleSheet } from 'react-native';

export const ArabicTextInput: React.FC<TextInputProps> = ({ style, ...props }) => {
  return (
    <RNTextInput
      style={[styles.input, style]}
      placeholderTextColor="#6B7280"
      // Enforces auto direction matching input characters
      writingDirection="auto" 
      textBreakStrategy="simple"
      {...props}
    />
  );
};

const styles = StyleSheet.create({
  input: {
    fontFamily: 'Tajawal-Regular',
    fontSize: 16,
    paddingStart: 12,
    paddingEnd: 12,
    paddingTop: 10,
    paddingBottom: 10,
    borderWidth: 1,
    borderColor: '#374151',
    borderRadius: 8,
    backgroundColor: '#1F2937',
    color: '#F3F4F6',
    textAlign: 'right',
  },
});
```

#### Reusable Icon Wrapper: `mobile/components/RTLIcon.tsx`
Automatically flips icons horizontally when system layout is in RTL mode.
```typescript
import React from 'react';
import { View, StyleProp, ViewStyle, I18nManager } from 'react-native';

interface RTLIconProps {
  IconComponent: React.ComponentType<any>;
  name: string;
  size?: number;
  color?: string;
  style?: StyleProp<ViewStyle>;
}

export const RTLIcon: React.FC<RTLIconProps> = ({
  IconComponent,
  name,
  size = 24,
  color = '#D4AF37',
  style,
}) => {
  const isRTL = I18nManager.isRTL;
  
  return (
    <View style={[{ transform: [{ scaleX: isRTL ? -1 : 1 }] }, style]}>
      <IconComponent name={name} size={size} color={color} />
    </View>
  );
};
```

#### Custom Colors Constant: `mobile/constants/Colors.ts`
Applies Gulf-region cultural ergonomically approved colors:
```typescript
export const Colors = {
  // Cultural color associations
  success: '#10B981',       // Green (emerald) - indicating completed campaigns/applications
  luxury: {
    gold: '#D4AF37',        // Metallic Gold accent
    sand: '#C5A880',        // Desert Sand highlight
    black: '#111827',       // Deep Charcoal primary background
  },
  trust: '#2563EB',         // Royal Blue - links, info boxes
  error: '#EF4444',         // Red (crimson) - strict errors only

  // Component styling
  background: '#111827',
  cardBackground: '#1F2937',
  textPrimary: '#F9FAFB',
  textSecondary: '#D1D5DB',
  border: '#374151',
};
```

---

## 4. Fetching and Displaying Data from FastAPI Backend
The mobile client fetches stats, campaigns, and jobs from the FastAPI backend (running on port `8000`).

### A. Environment API URL Selection (Avoid Localhost Pitfall)
To connect to the local FastAPI backend from mobile devices/emulators:
- **Android Emulator**: Use `http://10.0.2.2:8000`
- **iOS Simulator**: Use `http://localhost:8000`
- **Physical Device**: Use `http://<YOUR_LOCAL_IP>:8000`

### B. Custom Fetch Hook: `mobile/hooks/useApi.ts`
This hook wraps standard fetches, appending the correct base URL.
```typescript
import { useState, useEffect, useCallback } from 'react';
import { Platform } from 'react-native';

// Adjust default backend base url depending on host platform
const getBaseUrl = () => {
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000'; // Loopback to development machine
  }
  return 'http://localhost:8000'; // Default iOS Simulator / Web localhost
};

const BASE_URL = getBaseUrl();

export function useApi<T>(endpoint: string, lazy: boolean = false) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(!lazy);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (params?: Record<string, string | number>) => {
    setLoading(true);
    setError(null);

    let url = `${BASE_URL}${endpoint}`;
    if (params) {
      const query = Object.keys(params)
        .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key].toString())}`)
        .join('&');
      url += `?${query}`;
    }

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP Error Status: ${response.status}`);
      }

      const json = await response.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    if (!lazy) {
      fetchData();
    }
  }, [fetchData, lazy]);

  return { data, loading, error, refetch: fetchData };
}
```

### C. Dashboard Screen: `mobile/app/(tabs)/index.tsx`
Renders stats, active campaign status, and matching jobs using logical style configurations.

```typescript
import React from 'react';
import { View, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ArabicText } from '../../components/ArabicText';
import { Container } from '../../components/Container';
import { useApi } from '../../hooks/useApi';
import { Colors } from '../../constants/Colors';

interface StatsResponse {
  apps_sent: number;
  interviews: number;
  replies: number;
  match_rate: number;
  campaign: {
    id: number;
    status: string;
  } | null;
}

export default function DashboardScreen() {
  // Replace 'usr_dev_test' with dynamic authenticated user id
  const userId = 'usr_dev_test'; 
  
  const { data: stats, loading, error, refetch } = useApi<StatsResponse>(
    `/api/user/stats`,
    false
  );

  const handleRefresh = () => {
    refetch({ user_id: userId });
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView 
        contentContainerStyle={styles.container}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={handleRefresh} tintColor={Colors.luxury.gold} />
        }
      >
        {/* Header section */}
        <View style={styles.header}>
          <ArabicText variant="title" style={styles.title}>
            لوحة التحكم
          </ArabicText>
          <ArabicText variant="caption" style={styles.subtitle}>
            متابعة حالة حملات التوظيف التلقائية والفرص المطابقة
          </ArabicText>
        </View>

        {error && (
          <View style={styles.errorBox}>
            <ArabicText variant="bold" style={{ color: Colors.error }}>
              خطأ في الاتصال بالخادم
            </ArabicText>
            <ArabicText variant="caption" style={{ color: Colors.error }}>
              {error}
            </ArabicText>
          </View>
        )}

        {loading && !stats ? (
          <ActivityIndicator size="large" color={Colors.luxury.gold} style={styles.loader} />
        ) : stats ? (
          <>
            {/* Quick Stats Grid */}
            <View style={styles.grid}>
              <View style={styles.card}>
                <ArabicText variant="caption" style={styles.cardLabel}>
                  الطلبات المرسلة
                </ArabicText>
                <ArabicText variant="title" style={[styles.cardVal, { color: Colors.trust }]}>
                  {stats.apps_sent}
                </ArabicText>
              </View>

              <View style={styles.card}>
                <ArabicText variant="caption" style={styles.cardLabel}>
                  المقابلات الجارية
                </ArabicText>
                <ArabicText variant="title" style={[styles.cardVal, { color: Colors.success }]}>
                  {stats.interviews}
                </ArabicText>
              </View>

              <View style={styles.card}>
                <ArabicText variant="caption" style={styles.cardLabel}>
                  نسبة الملاءمة
                </ArabicText>
                <ArabicText variant="title" style={[styles.cardVal, { color: Colors.luxury.gold }]}>
                  {stats.match_rate}%
                </ArabicText>
              </View>
            </View>

            {/* Campaign Status */}
            <View style={styles.campaignContainer}>
              <ArabicText variant="bold" style={styles.sectionHeader}>
                الحملة الحالية
              </ArabicText>
              <View style={styles.campaignCard}>
                <View style={styles.row}>
                  <ArabicText variant="body">حالة الحملة:</ArabicText>
                  <ArabicText 
                    variant="bold" 
                    style={{ 
                      color: stats.campaign?.status === 'active' ? Colors.success : Colors.textSecondary 
                    }}
                  >
                    {stats.campaign?.status === 'active' ? 'نشطة (الطيار الآلي)' : 'غير نشطة'}
                  </ArabicText>
                </View>
                {stats.campaign?.status !== 'active' && (
                  <TouchableOpacity style={styles.ctaButton}>
                    <ArabicText variant="bold" style={styles.ctaText}>
                      تفعيل الطيار الآلي
                    </ArabicText>
                  </TouchableOpacity>
                )}
              </View>
            </View>
          </>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  container: {
    paddingStart: 20, // Logical Property
    paddingEnd: 20,   // Logical Property
    paddingTop: 10,
    paddingBottom: 30,
  },
  header: {
    marginBottom: 20,
  },
  title: {
    textAlign: 'right',
    color: Colors.textPrimary,
  },
  subtitle: {
    textAlign: 'right',
    color: Colors.textSecondary,
    marginTop: 4,
  },
  loader: {
    marginVertical: 40,
  },
  errorBox: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderWidth: 1,
    borderColor: Colors.error,
    borderRadius: 8,
    paddingStart: 16,
    paddingEnd: 16,
    paddingTop: 12,
    paddingBottom: 12,
    marginBottom: 20,
  },
  grid: {
    flexDirection: 'row-reverse', // Flow RTL natively in grid layout
    justifyContent: 'space-between',
    marginBottom: 20,
    gap: 10,
  },
  card: {
    flex: 1,
    backgroundColor: Colors.cardBackground,
    borderRadius: 8,
    paddingStart: 12,
    paddingEnd: 12,
    paddingTop: 16,
    paddingBottom: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  cardLabel: {
    color: Colors.textSecondary,
    fontSize: 14,
    marginBottom: 6,
    textAlign: 'center',
  },
  cardVal: {
    fontSize: 24,
    textAlign: 'center',
  },
  campaignContainer: {
    marginTop: 10,
  },
  sectionHeader: {
    color: Colors.textPrimary,
    marginBottom: 10,
  },
  campaignCard: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 8,
    paddingStart: 16,
    paddingEnd: 16,
    paddingTop: 16,
    paddingBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  row: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  ctaButton: {
    backgroundColor: Colors.luxury.gold,
    borderRadius: 8,
    paddingTop: 12,
    paddingBottom: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  ctaText: {
    color: '#000',
    fontSize: 16,
  },
});
```

---

## 5. Summary and Execution Verification
Upon initialization of the app in `mobile/`:
1. Use `npm install` for node dependencies and `npx expo install` for expo-supported wrappers.
2. The app loads Cairo and Tajawal fonts on startup.
3. Every screen layout employs the custom components wrapping text and inputs to prevent layout regression or violations of the `AGENTS.md` rules.
4. Developers should test locally on iOS simulators or Android Emulators verifying that layout mirrors smoothly between Arabic and English locales.
