/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',

  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: '/health',
        destination: `${backendUrl}/health`,
      },
      {
        source: '/security/:path*',
        destination: `${backendUrl}/security/:path*`,
      },
      {
        source: '/support/:path*',
        destination: `${backendUrl}/support/:path*`,
      },
      {
        source: '/cart-recovery/:path*',
        destination: `${backendUrl}/cart-recovery/:path*`,
      },
      {
        source: '/shopify/:path*',
        destination: `${backendUrl}/shopify/:path*`,
      },
    ]
  },

  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'cdn.shopify.com' },
    ],
  },

  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
  },
}

export default nextConfig
