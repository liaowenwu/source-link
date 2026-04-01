import CryptoJS from 'crypto-js'

const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
type AesWordArray = ReturnType<typeof CryptoJS.enc.Utf8.parse>

function randomString(length = 32) {
  return Array.from({ length }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join('')
}

export function generateAesKey() {
  return CryptoJS.enc.Utf8.parse(randomString())
}

export function encryptBase64(wordArray: AesWordArray) {
  return CryptoJS.enc.Base64.stringify(wordArray)
}

export function decryptBase64(value: string) {
  return CryptoJS.enc.Base64.parse(value)
}

export function encryptWithAes(message: string, aesKey: AesWordArray) {
  return CryptoJS.AES.encrypt(message, aesKey, {
    mode: CryptoJS.mode.ECB,
    padding: CryptoJS.pad.Pkcs7,
  }).toString()
}

export function decryptWithAes(message: string, aesKey: AesWordArray) {
  return CryptoJS.AES.decrypt(message, aesKey, {
    mode: CryptoJS.mode.ECB,
    padding: CryptoJS.pad.Pkcs7,
  }).toString(CryptoJS.enc.Utf8)
}
