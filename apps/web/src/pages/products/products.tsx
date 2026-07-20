import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Search,
  Pencil,
  Archive,
  Package,
  Plus,
  RotateCcw,
  Tag,
  Trash2,
} from 'lucide-react'
import {
  Button,
  Input,
  Card,
  Modal,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Skeleton,
  Badge,
  Select,
} from '@/components/ui'
import { useToast } from '@/hooks/useToast'
import { useSettings } from '@/hooks/useSettings'
import { getErrorMessage } from '@/lib/axios'
import { formatCurrency } from '@/lib/utils'
import { productsApi } from '@/services'
import type {
  CreateProductCategoryInput,
  CreateProductInput,
  Product,
  ProductCategory,
} from '@/types'

const PAGE_SIZE = 50

export function ProductsPage() {
  const queryClient = useQueryClient()
  const { success, error } = useToast()
  const { currency } = useSettings()
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const [page, setPage] = useState(0)
  const [createOpen, setCreateOpen] = useState(false)
  const [createFormKey, setCreateFormKey] = useState(0)
  const [editProduct, setEditProduct] = useState<Product | null>(null)
  const [categoryModalOpen, setCategoryModalOpen] = useState(false)
  const [newCategoryName, setNewCategoryName] = useState('')

  const { data: categoriesData } = useQuery({
    queryKey: ['product-categories'],
    queryFn: () => productsApi.listCategories(),
  })

  const { data: productPage, isLoading } = useQuery({
    queryKey: ['products', page, search, categoryFilter, includeInactive],
    queryFn: () =>
      productsApi.list({
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        q: search || undefined,
        category_id: categoryFilter || undefined,
        include_inactive: includeInactive,
      }),
  })

  const categories = categoriesData?.items ?? []
  const products = productPage?.items ?? []
  const totalProducts = productPage?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(totalProducts / PAGE_SIZE))

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['products'] })
    queryClient.invalidateQueries({ queryKey: ['product-categories'] })
  }

  const createMutation = useMutation({
    mutationFn: (input: CreateProductInput) => productsApi.create(input),
    onSuccess: () => {
      invalidate()
      setCreateFormKey((key) => key + 1)
      setCreateOpen(false)
      success('Product created')
    },
    onError: (err: unknown) => error(getErrorMessage(err)),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: Partial<CreateProductInput> }) =>
      productsApi.update(id, input),
    onSuccess: () => {
      invalidate()
      setEditProduct(null)
      success('Product updated')
    },
    onError: (err: unknown) => error(getErrorMessage(err)),
  })

  const archiveMutation = useMutation({
    mutationFn: (id: string) => productsApi.archive(id),
    onSuccess: () => {
      invalidate()
      success('Product archived')
    },
    onError: (err: unknown) => error(getErrorMessage(err)),
  })

  const reactivateMutation = useMutation({
    mutationFn: (id: string) => productsApi.reactivate(id),
    onSuccess: () => {
      invalidate()
      success('Product reactivated')
    },
    onError: (err: unknown) => error(getErrorMessage(err)),
  })

  const createCategoryMutation = useMutation({
    mutationFn: (input: CreateProductCategoryInput) => productsApi.createCategory(input),
    onSuccess: () => {
      invalidate()
      setNewCategoryName('')
      success('Category created')
    },
    onError: (err: unknown) => error(getErrorMessage(err)),
  })

  const deleteCategoryMutation = useMutation({
    mutationFn: (id: string) => productsApi.deleteCategory(id),
    onSuccess: () => {
      invalidate()
      success('Category deleted')
    },
    onError: (err: unknown) => error(getErrorMessage(err)),
  })

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Products</h1>
          <p className="text-muted-foreground mt-1">
            Manage your catalog for faster invoicing
          </p>
        </div>
        <Button
          onClick={() => {
            setCreateFormKey((key) => key + 1)
            setCreateOpen(true)
          }}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Product
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search products..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setPage(0)
                }}
                className="pl-10"
              />
            </div>
            <Select
              options={[
                { value: '', label: 'All categories' },
                ...categories.map((category) => ({
                  value: category.id,
                  label: category.name,
                })),
              ]}
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value)
                setPage(0)
              }}
              className="w-[180px]"
            />
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={includeInactive}
                onChange={(e) => {
                  setIncludeInactive(e.target.checked)
                  setPage(0)
                }}
              />
              Show archived
            </label>
          </div>

          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-14 w-full rounded-lg" />
              ))}
            </div>
          ) : products.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Package className="h-10 w-10 text-muted-foreground" />
              <h3 className="mt-4 text-base font-semibold">No products yet</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Add products to bill customers faster
              </p>
              <Button className="mt-4" onClick={() => setCreateOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Product
              </Button>
            </div>
          ) : (
            <Card>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>SKU</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Price</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[100px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {products.map((product) => (
                      <TableRow key={product.id}>
                        <TableCell className="font-medium">{product.name}</TableCell>
                        <TableCell className="text-muted-foreground">
                          {product.sku || '—'}
                        </TableCell>
                        <TableCell>{product.category_name || '—'}</TableCell>
                        <TableCell className="font-mono">
                          {formatCurrency(product.unit_price, currency)}
                        </TableCell>
                        <TableCell>
                          {product.is_active ? (
                            <Badge variant="success">Active</Badge>
                          ) : (
                            <Badge variant="secondary">Archived</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => setEditProduct(product)}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                            {product.is_active ? (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => archiveMutation.mutate(product.id)}
                              >
                                <Archive className="h-4 w-4" />
                              </Button>
                            ) : (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => reactivateMutation.mutate(product.id)}
                              >
                                <RotateCcw className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </Card>
          )}

          {totalPages > 1 && (
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page + 1 >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </div>

        <Card className="h-fit p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Tag className="h-4 w-4 text-muted-foreground" />
              <h2 className="font-semibold">Categories</h2>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCategoryModalOpen(true)}
            >
              Manage
            </Button>
          </div>
          {categories.length === 0 ? (
            <p className="text-sm text-muted-foreground">No categories yet</p>
          ) : (
            <ul className="space-y-2">
              {categories.map((category) => (
                <li
                  key={category.id}
                  className="flex items-center justify-between text-sm"
                >
                  <span>{category.name}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => deleteCategoryMutation.mutate(category.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <ProductFormModal
        key={createFormKey}
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        categories={categories}
        onSubmit={(data) => createMutation.mutate(data)}
        loading={createMutation.isPending}
        title="Add Product"
      />

      {editProduct && (
        <ProductFormModal
          key={editProduct.id}
          open={!!editProduct}
          onClose={() => setEditProduct(null)}
          categories={categories}
          product={editProduct}
          onSubmit={(data) =>
            updateMutation.mutate({ id: editProduct.id, input: data })
          }
          loading={updateMutation.isPending}
          title="Edit Product"
        />
      )}

      <Modal
        open={categoryModalOpen}
        onClose={() => setCategoryModalOpen(false)}
        title="Add Category"
      >
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault()
            if (!newCategoryName.trim()) return
            createCategoryMutation.mutate({ name: newCategoryName.trim() })
          }}
        >
          <Input
            placeholder="Category name"
            value={newCategoryName}
            onChange={(e) => setNewCategoryName(e.target.value)}
            required
          />
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setCategoryModalOpen(false)}
            >
              Close
            </Button>
            <Button type="submit" disabled={createCategoryMutation.isPending}>
              Add Category
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

function ProductFormModal({
  open,
  onClose,
  categories,
  product,
  onSubmit,
  loading,
  title,
}: {
  open: boolean
  onClose: () => void
  categories: ProductCategory[]
  product?: Product
  onSubmit: (data: CreateProductInput) => void
  loading: boolean
  title: string
}) {
  const [formData, setFormData] = useState<CreateProductInput>({
    name: product?.name ?? '',
    sku: product?.sku ?? '',
    description: product?.description ?? '',
    unit_price: product ? Number(product.unit_price) : 0,
    category_id: product?.category_id ?? '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      ...formData,
      sku: formData.sku?.trim() || undefined,
      description: formData.description?.trim() || undefined,
      category_id: formData.category_id || undefined,
    })
  }

  return (
    <Modal open={open} onClose={onClose} title={title}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Name</label>
          <Input
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium">SKU</label>
          <Input
            value={formData.sku ?? ''}
            onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
            placeholder="Optional"
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Unit price</label>
          <Input
            type="number"
            step="0.01"
            min="0"
            className="font-mono"
            value={formData.unit_price || ''}
            onChange={(e) =>
              setFormData({
                ...formData,
                unit_price: parseFloat(e.target.value) || 0,
              })
            }
            required
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Category</label>
          <Select
            options={[
              { value: '', label: 'No category' },
              ...categories.map((category) => ({
                value: category.id,
                label: category.name,
              })),
            ]}
            value={formData.category_id ?? ''}
            onChange={(e) =>
              setFormData({ ...formData, category_id: e.target.value })
            }
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Description</label>
          <Input
            value={formData.description ?? ''}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
            placeholder="Optional"
          />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading || !formData.name}>
            {loading ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
