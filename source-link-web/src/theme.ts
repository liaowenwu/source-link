import { darkTheme, type GlobalThemeOverrides } from 'naive-ui'

export const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#1570ef',
    primaryColorHover: '#2e90fa',
    primaryColorPressed: '#175cd3',
    primaryColorSuppl: '#3b82f6',
    infoColor: '#2e90fa',
    successColor: '#12b76a',
    warningColor: '#f79009',
    errorColor: '#f04438',
    borderRadius: '12px',
    borderRadiusSmall: '10px',
    fontFamily: '"IBM Plex Sans", "Microsoft YaHei UI", "PingFang SC", sans-serif',
    fontFamilyMono: '"JetBrains Mono", "Cascadia Code", monospace',
    bodyColor: '#f5f8fc',
    cardColor: '#ffffff',
    modalColor: '#ffffff',
    tableColor: '#ffffff',
    popoverColor: '#ffffff',
    borderColor: '#dfe7f4',
    dividerColor: '#e4ecf7',
    textColorBase: '#182230',
    textColor1: '#182230',
    textColor2: '#475467',
    textColor3: '#667085',
    placeholderColor: '#98a2b3',
  },
  Layout: {
    siderColor: '#ffffff',
    headerColor: '#ffffff',
    color: '#f5f8fc',
  },
  Card: {
    borderRadius: '16px',
    paddingMedium: '18px',
  },
  DataTable: {
    thColor: '#f2f6fd',
    tdColor: '#ffffff',
    tdColorModal: '#ffffff',
    borderColor: '#e0e8f5',
  },
  Button: {
    fontWeight: '600',
  },
  Input: {
    borderHover: '#84caff',
    borderFocus: '#1570ef',
    boxShadowFocus: '0 0 0 2px rgba(21, 112, 239, 0.18)',
  },
  Select: {
    peers: {
      InternalSelection: {
        borderHover: '#84caff',
        borderFocus: '#1570ef',
      },
    },
  },
  Tag: {
    borderRadius: '999px',
  },
}

export const adminDarkTheme = darkTheme
