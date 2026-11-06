import type { AppProps } from 'next/app'
import '../styles/globals.css'
import { SearchQueryContextProvider } from '@/context/search-query-context'
import { CartProvider } from '@/context/cart-context'

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <SearchQueryContextProvider>
      <CartProvider>
        <Component {...pageProps} />
      </CartProvider>
    </SearchQueryContextProvider>
  )
}
