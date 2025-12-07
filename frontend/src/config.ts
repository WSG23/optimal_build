import { z } from 'zod'

const envSchema = z.object({
  VITE_API_BASE_URL: z.string().url().default('http://localhost:8000'),
  VITE_DEV_HOST: z.string().optional(),
  FRONTEND_PORT: z.string().optional(),
  BACKEND_PORT: z.string().optional(),
  MODE: z.enum(['development', 'production', 'test']).default('development'),
})

const envVars = {
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_DEV_HOST: import.meta.env.VITE_DEV_HOST,
  FRONTEND_PORT: import.meta.env.FRONTEND_PORT,
  BACKEND_PORT: import.meta.env.BACKEND_PORT,
  MODE: import.meta.env.MODE,
}

const parsedEnv = envSchema.safeParse(envVars)

if (!parsedEnv.success) {
  console.error('❌ Invalid environment variables:', parsedEnv.error.format())
  // In production, we might want to throw to prevent startup with bad config
  if (import.meta.env.PROD) {
      throw new Error('Invalid environment variables')
  }
}

export const config = {
  apiBaseUrl: parsedEnv.success ? parsedEnv.data.VITE_API_BASE_URL : 'http://localhost:8000',
  mode: parsedEnv.success ? parsedEnv.data.MODE : 'development',
  isProduction: import.meta.env.PROD,
  isDev: import.meta.env.DEV,
}
