import JSEncrypt from 'jsencrypt'

const publicKey = import.meta.env.VITE_APP_RSA_PUBLIC_KEY
const privateKey = import.meta.env.VITE_APP_RSA_PRIVATE_KEY

export function encrypt(text: string) {
  const encryptor = new JSEncrypt()
  encryptor.setPublicKey(publicKey)
  return encryptor.encrypt(text)
}

export function decrypt(text: string) {
  const encryptor = new JSEncrypt()
  encryptor.setPrivateKey(privateKey)
  return encryptor.decrypt(text)
}
