import { api } from '@/lib/axios'
import type {
  CreateProductCategoryInput,
  CreateProductInput,
  PaginatedResponse,
  Product,
  ProductCategory,
} from '@/types'

export const productsApi = {
  listCategories: async () => {
    const { data } = await api.get<{ items: ProductCategory[]; total: number }>(
      '/product-categories'
    )
    return data
  },

  createCategory: async (input: CreateProductCategoryInput) => {
    const { data } = await api.post<ProductCategory>('/product-categories', input)
    return data
  },

  updateCategory: async (id: string, input: Partial<CreateProductCategoryInput>) => {
    const { data } = await api.patch<ProductCategory>(`/product-categories/${id}`, input)
    return data
  },

  deleteCategory: async (id: string) => {
    await api.delete(`/product-categories/${id}`)
  },

  list: async (params?: {
    limit?: number
    offset?: number
    q?: string
    category_id?: string
    include_inactive?: boolean
  }) => {
    const { data } = await api.get<PaginatedResponse<Product>>('/products', { params })
    return data
  },

  search: async (query: string) => {
    const { data } = await api.get<Product[]>('/products/search', {
      params: { q: query },
    })
    return data
  },

  get: async (id: string) => {
    const { data } = await api.get<Product>(`/products/${id}`)
    return data
  },

  create: async (input: CreateProductInput) => {
    const { data } = await api.post<Product>('/products', input)
    return data
  },

  update: async (id: string, input: Partial<CreateProductInput>) => {
    const { data } = await api.patch<Product>(`/products/${id}`, input)
    return data
  },

  archive: async (id: string) => {
    await api.delete(`/products/${id}`)
  },

  reactivate: async (id: string) => {
    const { data } = await api.post<Product>(`/products/${id}/reactivate`)
    return data
  },
}
