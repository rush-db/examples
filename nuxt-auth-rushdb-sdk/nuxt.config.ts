import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
    srcDir: 'src/',
    ssr: false,
    modules: [
        '@nuxtjs/tailwindcss',
        'radix-vue/nuxt'
    ],
    runtimeConfig: {
        rushdbToken: process.env.RUSHDB_API_TOKEN,
        rushdbBaseUrl: process.env.RUSHDB_BASE_URL,
        authSecret: process.env.AUTH_SECRET,
        port: Number(process.env.PORT || 3007)
    }
});