import removeImports from 'next-remove-imports'

/** @type {import('next').NextConfig} */
const nextConfig = removeImports({
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  experimental: {
    webpackBuildWorker: true,
    parallelServerBuildTraces: true,
    parallelServerCompiles: true,
  },
  // webpack: (config) => {
  //   // Allow importing CSS from @uiw packages
  //   config.module.rules.push({
  //     test: /\.css$/,
  //     include: [/node_modules\/@uiw/],
  //     use: ['style-loader', 'css-loader'],
  //   })
  //   return config
  // },
  // transpilePackages: ['@uiw/react-md-editor', '@uiw/react-markdown-preview'],
})

export default nextConfig
