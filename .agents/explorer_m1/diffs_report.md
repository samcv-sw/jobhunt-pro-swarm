### Diff for `auth-v2.css` vs `auth-v2-rtl.css`

```diff
@@ -41,2 +41,2 @@

-left:0;
-right:0;
+inset-inline-start:0;
+inset-inline-end:0;
@@ -197 +197 @@

-right:12px;
+inset-inline-end:12px;
@@ -263 +263 @@

-left:50%;
+inset-inline-start:50%;
@@ -348 +348 @@

-left:0;
+inset-inline-start:0;
@@ -351 +351 @@

-right:0;
+inset-inline-end:0;
@@ -451 +451 @@

-right:-6px;
+inset-inline-end:-6px;
```

### Diff for `cyberpunk.css` vs `cyberpunk-rtl.css`

```diff
@@ -28 +28 @@

+--cyber-text-bright:#ffffff;
@@ -77 +77 @@

-inset-block-start:0 !important;
+top:0 !important;
@@ -89 +89 @@

-inset-block-start:0 !important;
+top:0 !important;
@@ -114,2 +114,2 @@

-border-block-end:1px solid var(--cyber-border) !important;
-padding-block-end:0.5rem !important;
+border-bottom:1px solid var(--cyber-border) !important;
+padding-bottom:0.5rem !important;
@@ -165 +165 @@

-inset-block-start:0 !important;
+top:0 !important;
@@ -311 +311 @@

-inset-block-start:-2px !important;
+top:-2px !important;
@@ -314 +314 @@

-inset-block-end:-2px !important;
+bottom:-2px !important;
@@ -325 +325 @@

-inset-block-start:0 !important;
+top:0 !important;
@@ -328 +328 @@

-inset-block-end:0 !important;
+bottom:0 !important;
@@ -337 +337 @@

-border-block-end:1px solid var(--cyber-border) !important;
+border-bottom:1px solid var(--cyber-border) !important;
@@ -350 +350 @@

-border-block-end:2px solid var(--cyber-cyan) !important;
+border-bottom:2px solid var(--cyber-cyan) !important;
@@ -388 +388 @@

-border-block-end:2px solid var(--cyber-border-cyan) !important;
+border-bottom:2px solid var(--cyber-border-cyan) !important;
@@ -391 +391 @@

-border-block-end:1px solid var(--cyber-border) !important;
+border-bottom:1px solid var(--cyber-border) !important;
@@ -496 +496 @@

-border-block-start-color:var(--cyber-cyan) !important;
+border-top-color:var(--cyber-cyan) !important;
@@ -517 +517 @@

-inset-block-start:0 !important;
+top:0 !important;
@@ -531 +531 @@

-inset-block-end:120% !important;
+bottom:120% !important;
@@ -562 +562 @@

-inset-block-start:0 !important;
+top:0 !important;
@@ -612 +612 @@

-border-block-start:1px solid var(--cyber-border) !important;
+border-top:1px solid var(--cyber-border) !important;
@@ -622 +622 @@

-border-block-end:1px solid var(--cyber-border) !important;
+border-bottom:1px solid var(--cyber-border) !important;
@@ -625 +625 @@

-border-block-start:1px solid var(--cyber-border) !important;
+border-top:1px solid var(--cyber-border) !important;
@@ -680 +680 @@

-inset-block-start:-12px !important;
+top:-12px !important;
@@ -701 +701 @@

-inset-block-start:0 !important;
+top:0 !important;
@@ -743 +743 @@

-border-block-end:1px solid rgba(0, 255, 65, 0.2) !important;
+border-bottom:1px solid rgba(0, 255, 65, 0.2) !important;
@@ -1052 +1052 @@

-inset-block-start:0;
+top:0;
@@ -1055 +1055 @@

-inset-block-end:0;
+bottom:0;
@@ -1071 +1071 @@

-margin-block-end:60px;
+margin-bottom:60px;
@@ -1077 +1077 @@

-margin-block-end:15px;
+margin-bottom:15px;
@@ -1089 +1089 @@

-margin-block-end:60px;
+margin-bottom:60px;
@@ -1108 +1108 @@

-margin-block-end:15px;
+margin-bottom:15px;
@@ -1122 +1122 @@

-margin-block-end:15px;
+margin-bottom:15px;
@@ -1137 +1137 @@

-margin-block-end:20px;
+margin-bottom:20px;
@@ -1153 +1153 @@

-margin-block-end:50px;
+margin-bottom:50px;
@@ -1161 +1161 @@

-margin-block-end:20px;
+margin-bottom:20px;
@@ -1168 +1168 @@

-margin-block-end:25px;
+margin-bottom:25px;
@@ -1193 +1193 @@

-margin-block-end:50px;
+margin-bottom:50px;
@@ -1206 +1206 @@

-margin-block-end:25px;
+margin-bottom:25px;
@@ -1209 +1209 @@

-margin-block-end:25px;
+margin-bottom:25px;
@@ -1213 +1213 @@

-margin-block-end:10px;
+margin-bottom:10px;
@@ -1226,3 +1226,3 @@

-margin-block-start:40px;
-padding-block-start:40px;
-border-block-start:1px solid var(--border);
+margin-top:40px;
+padding-top:40px;
+border-top:1px solid var(--border);
@@ -1239 +1239 @@

-margin-block-end:15px;
+margin-bottom:15px;
@@ -1243 +1243 @@

-margin-block-end:25px;
+margin-bottom:25px;
@@ -1262,2 +1262,2 @@

-border-block-start:1px solid var(--border);
-margin-block-start:60px;
+border-top:1px solid var(--border);
+margin-top:60px;
@@ -1279 +1279 @@

-margin-block-end:25px;
+margin-bottom:25px;
@@ -1300 +1300 @@

-margin-block-end:10px;
+margin-bottom:10px;
@@ -1318,46 +1317,0 @@

-.glass-panel{
-background:rgba(10, 10, 15, 0.45);
-backdrop-filter:blur(20px) saturate(150%);
--webkit-backdrop-filter:blur(20px) saturate(150%);
-border:1px solid rgba(255, 255, 255, 0.05);
-box-shadow:inset 0 1px 0 rgba(255, 255, 255, 0.1), 0 8px 32px 0 rgba(0, 0, 0, 0.37);
-transition:all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
-}
-.glass-panel:hover{
-box-shadow:inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 8px 32px 0 rgba(0, 240, 255, 0.2);
-transform:translateY(-2px);
-}
-.btn-cyber-premium{
-position:relative;
-overflow:hidden;
-transition:all 0.3s ease;
-}
-.btn-cyber-premium::after{
-content:'';
-position:absolute;
-top:-50%;
-inset-inline-start:-50%;
-width:200%;
-height:200%;
-background:conic-gradient(transparent, rgba(0, 240, 255, 0.3), transparent 30%);
-animation:rotate 4s linear infinite;
-opacity:0;
-transition:opacity 0.3s;
-}
-.btn-cyber-premium:hover::after{
-opacity:1;
-}
-@keyframes rotate{
-100%{
-transform:rotate(360deg);
-}
-}
-.dir-icon {
-transform: scaleX(var(--text-x-direction, 1));
-}
-[dir='rtl'] {
-}
-[dir='ltr'] {
-}
```

### Diff for `dashboard-v4.css` vs `dashboard-v4-rtl.css`

```diff
@@ -277,2 +277,2 @@

-left:0;
-right:0;
+inset-inline-start:0;
+inset-inline-end:0;
@@ -459 +459 @@

-right:24px;
+inset-inline-end:24px;
@@ -560,2 +560,2 @@

-left:0;
-right:0;
+inset-inline-start:0;
+inset-inline-end:0;
@@ -585 +585 @@

-left:50%;
+inset-inline-start:50%;
@@ -623 +623 @@

-left:50%;
+inset-inline-start:50%;
@@ -750 +750 @@

-left:3px;
+inset-inline-start:3px;
@@ -776 +776 @@

-right:0;
+inset-inline-end:0;
@@ -811 +811 @@

-text-align:left;
+text-align:start;
@@ -863,2 +863,2 @@

-margin-left:auto;
-margin-right:auto;
+margin-inline-start:auto;
+margin-inline-end:auto;
@@ -955 +955 @@

-text-align:left;
+text-align:start;
@@ -1039,2 +1039,2 @@

-right:12px;
-left:12px;
+inset-inline-end:12px;
+inset-inline-start:12px;
```

### Diff for `landing-v4.css` vs `landing-v4-rtl.css`

```diff
@@ -110 +110 @@

-left:0;
+inset-inline-start:0;
@@ -129 +129 @@

-left:0;
+inset-inline-start:0;
@@ -309 +309 @@

-left:-100px;
+inset-inline-start:-100px;
@@ -316 +316 @@

-right:-100px;
+inset-inline-end:-100px;
@@ -323 +323 @@

-left:50%;
+inset-inline-start:50%;
@@ -340 +340 @@

-left:50%;
+inset-inline-start:50%;
@@ -521 +521 @@

-left:0;
+inset-inline-start:0;
@@ -537 +537 @@

-margin-left:2px;
+margin-inline-start:2px;
@@ -584 +584 @@

-left:-50%;
+inset-inline-start:-50%;
@@ -634 +634 @@

-right:-28px;
+inset-inline-end:-28px;
@@ -760 +760 @@

-left:12%;
+inset-inline-start:12%;
@@ -853 +853 @@

-left:0;
+inset-inline-start:0;
@@ -1085 +1085 @@

-left:0;
+inset-inline-start:0;
@@ -1223 +1223 @@

-text-align:left;
+text-align:start;
@@ -1298,2 +1298,2 @@

-text-align:left;
-padding-left:24px;
+text-align:start;
+padding-inline-start:24px;
@@ -1306,2 +1306,2 @@

-border-left:1px solid rgba(0, 240, 255, 0.15);
-border-right:1px solid rgba(0, 240, 255, 0.15);
+border-inline-start:1px solid rgba(0, 240, 255, 0.15);
+border-inline-end:1px solid rgba(0, 240, 255, 0.15);
@@ -1317,2 +1317,2 @@

-text-align:left;
-padding-left:24px;
+text-align:start;
+padding-inline-start:24px;
@@ -1324,2 +1324,2 @@

-border-left:1px solid rgba(0, 240, 255, 0.15);
-border-right:1px solid rgba(0, 240, 255, 0.15);
+border-inline-start:1px solid rgba(0, 240, 255, 0.15);
+border-inline-end:1px solid rgba(0, 240, 255, 0.15);
@@ -1400 +1400 @@

-left:50%;
+inset-inline-start:50%;
@@ -1480 +1480 @@

-text-align:left;
+text-align:start;
@@ -1611 +1611 @@

-left:0;
+inset-inline-start:0;
@@ -1633,2 +1633,2 @@

-padding-left:16px;
-border-left:2px solid rgba(0, 240, 255, 0.1);
+padding-inline-start:16px;
+border-inline-start:2px solid rgba(0, 240, 255, 0.1);
@@ -1817 +1817 @@

-left:50%;
+inset-inline-start:50%;
@@ -1872 +1872 @@

-left:-100%;
+inset-inline-start:-100%;
@@ -1879 +1879 @@

-left:100%;
+inset-inline-start:100%;
@@ -1908 +1908 @@

-text-align:left;
+text-align:start;
@@ -1988,2 +1988,2 @@

-margin-left:auto;
-margin-right:auto;
+margin-inline-start:auto;
+margin-inline-end:auto;
@@ -2046 +2046 @@

-left:0;
+inset-inline-start:0;
@@ -2202 +2202 @@

-text-align:left;
+text-align:start;
```

### Diff for `style.css` vs `style-rtl.css`

```diff
@@ -220 +220 @@

-padding-left:20px;
+padding-inline-start:20px;
@@ -241,2 +241,2 @@

-border-left:4px solid var(--blue);
-padding-left:16px;
+border-inline-start:4px solid var(--blue);
+padding-inline-start:16px;
```
