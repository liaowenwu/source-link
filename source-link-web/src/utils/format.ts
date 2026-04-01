import dayjs from 'dayjs'

export function formatDateTime(value?: string | number | null) {
  if (!value) {
    return '--'
  }
  return dayjs(value).format('YYYY-MM-DD HH:mm:ss')
}

export function formatBooleanStatus(value?: string | number | boolean | null) {
  if (value === '0' || value === 0 || value === true) {
    return '启用'
  }
  if (value === '1' || value === 1 || value === false) {
    return '停用'
  }
  return '--'
}

export function formatVisible(value?: string | null) {
  if (value === '0') {
    return '显示'
  }
  if (value === '1') {
    return '隐藏'
  }
  return '--'
}

export function splitToArray(value?: string | Array<string | number> | null) {
  if (!value) {
    return []
  }
  return Array.isArray(value)
    ? value
    : value
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
}
