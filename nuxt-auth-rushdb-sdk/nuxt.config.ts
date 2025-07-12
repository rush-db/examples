import { defineNuxtConfig } from 'nuxt/config'
import type { NuxtPage } from 'nuxt/schema'

export default defineNuxtConfig({
    hooks: {
        'pages:extend' (pages) {
            function setMiddleware (pages: NuxtPage[]) {
                for (const page of pages) {
                        page.meta ||= {}
                        page.meta.middleware = ['auth-client']
                    if (page.children) {
                        setMiddleware(page.children)
                    }
                }
            }
            setMiddleware(pages)
        }
    },
    srcDir: 'src/',
    ssr: false,
    modules: [
        '@nuxtjs/tailwindcss'
    ],
    runtimeConfig: {
        rushdbToken: process.env.RUSHDB_API_TOKEN,
        rushdbBaseUrl: process.env.RUSHDB_BASE_URL,
        authSecret: process.env.AUTH_SECRET,
        port: Number(process.env.PORT || 3007)
    }
});