'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Eye,
  Edit3,
  Split,
  Maximize2,
  Minimize2,
  FileText,
  PenTool,
  Settings,
  Plus,
  X,
  Hash,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTheme } from 'next-themes'

import '@uiw/react-md-editor/markdown-editor.css'
import '@uiw/react-markdown-preview/markdown.css'
import dynamic from 'next/dynamic'

import * as commands from '@uiw/react-md-editor/commands'

const MDEditor = dynamic(() => import('@uiw/react-md-editor'), { ssr: false })

interface FrontmatterField {
  key: string
  value: string | boolean | number
  type: 'string' | 'boolean' | 'number' | 'array'
}

interface MarkdownEditorProps {
  value?: string
  onChange: (value: string) => void
  title?: string
  className?: string
  placeholder?: string
  readOnly?: boolean
  showStats?: boolean
  frontmatterFields?: FrontmatterField[]
  onFrontmatterChange?: (fields: FrontmatterField[]) => void
}

export function MarkdownEditor({
  value = '',
  onChange,
  title = 'Content',
  className,
  placeholder = 'Start writing your content...',
  readOnly = false,
  showStats = true,
  frontmatterFields = [],
  onFrontmatterChange,
}: MarkdownEditorProps) {
  const [mode, setMode] = useState<'edit' | 'preview' | 'split'>('split')
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showFrontmatterModal, setShowFrontmatterModal] = useState(false)
  const [localFrontmatterFields, setLocalFrontmatterFields] =
    useState<FrontmatterField[]>(frontmatterFields)
  const [stats, setStats] = useState({
    words: 0,
    characters: 0,
    charactersNoSpaces: 0,
    paragraphs: 0,
    readingTime: 0,
  })

  const { theme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  // Avoid hydration mismatch
  useEffect(() => {
    setMounted(true)
  }, [])

  // Get the current theme mode for the editor
  const getColorMode = () => {
    if (!mounted) return 'light' // Default during SSR
    if (resolvedTheme === 'dark') return 'dark'
    if (resolvedTheme === 'light') return 'light'
    // Fallback to system preference
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
    }
    return 'light'
  }

  // Parse frontmatter from content
  const parseFrontmatter = (content: string) => {
    const frontmatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n/
    const match = content.match(frontmatterRegex)

    if (match) {
      const frontmatterText = match[1]
      const contentWithoutFrontmatter = content.replace(frontmatterRegex, '')

      // Parse YAML-like frontmatter
      const fields: FrontmatterField[] = []
      const lines = frontmatterText.split('\n')

      for (const line of lines) {
        const trimmedLine = line.trim()
        if (trimmedLine && !trimmedLine.startsWith('#')) {
          const colonIndex = trimmedLine.indexOf(':')
          if (colonIndex > 0) {
            const key = trimmedLine.substring(0, colonIndex).trim()
            const valueStr = trimmedLine.substring(colonIndex + 1).trim()

            let value: string | boolean | number = valueStr
            let type: 'string' | 'boolean' | 'number' | 'array' = 'string'

            // Type detection
            if (valueStr === 'true' || valueStr === 'false') {
              value = valueStr === 'true'
              type = 'boolean'
            } else if (!isNaN(Number(valueStr)) && valueStr !== '') {
              value = Number(valueStr)
              type = 'number'
            } else if (valueStr.startsWith('[') && valueStr.endsWith(']')) {
              type = 'array'
              // Keep as string for now, could parse array later
            }

            fields.push({ key, value, type })
          }
        }
      }

      return { fields, content: contentWithoutFrontmatter }
    }

    return { fields: [], content }
  }

  // Generate frontmatter string
  const generateFrontmatter = (fields: FrontmatterField[]) => {
    if (fields.length === 0) return ''

    const frontmatterLines = fields.map((field) => {
      let valueStr = String(field.value)
      if (
        field.type === 'string' &&
        typeof field.value === 'string' &&
        field.value.includes(' ')
      ) {
        valueStr = `"${field.value}"`
      }
      return `${field.key}: ${valueStr}`
    })

    return `---\n${frontmatterLines.join('\n')}\n---\n\n`
  }

  // Update content with frontmatter
  const updateContentWithFrontmatter = (
    fields: FrontmatterField[],
    content: string
  ) => {
    const frontmatter = generateFrontmatter(fields)
    const { content: contentOnly } = parseFrontmatter(value)
    const newContent = frontmatter + (content || contentOnly)
    onChange(newContent)
  }

  // Initialize frontmatter fields from content
  useEffect(() => {
    const { fields } = parseFrontmatter(value)
    setLocalFrontmatterFields(fields)
  }, [value])

  // Calculate content statistics
  useEffect(() => {
    if (!value) {
      setStats({
        words: 0,
        characters: 0,
        charactersNoSpaces: 0,
        paragraphs: 0,
        readingTime: 0,
      })
      return
    }

    const { content } = parseFrontmatter(value)
    const contentToAnalyze = content || value

    const words = contentToAnalyze
      .trim()
      .split(/\s+/)
      .filter((word) => word.length > 0).length
    const characters = contentToAnalyze.length
    const charactersNoSpaces = contentToAnalyze.replace(/\s/g, '').length
    const paragraphs = contentToAnalyze
      .split(/\n\s*\n/)
      .filter((p) => p.trim().length > 0).length
    const readingTime = Math.ceil(words / 200) // Assuming 200 words per minute

    setStats({
      words,
      characters,
      charactersNoSpaces,
      paragraphs,
      readingTime,
    })
  }, [value])

  const getVisibleMode = () => {
    if (mode === 'edit') return 'edit'
    if (mode === 'preview') return 'preview'
    return 'live' // split mode
  }

  const addFrontmatterField = () => {
    const newField: FrontmatterField = {
      key: '',
      value: '',
      type: 'string',
    }
    setLocalFrontmatterFields([...localFrontmatterFields, newField])
  }

  const updateFrontmatterField = (
    index: number,
    updates: Partial<FrontmatterField>
  ) => {
    const updatedFields = [...localFrontmatterFields]
    updatedFields[index] = { ...updatedFields[index], ...updates }
    setLocalFrontmatterFields(updatedFields)
  }

  const removeFrontmatterField = (index: number) => {
    const updatedFields = localFrontmatterFields.filter((_, i) => i !== index)
    setLocalFrontmatterFields(updatedFields)
  }

  const saveFrontmatter = () => {
    const validFields = localFrontmatterFields.filter(
      (field) => field.key.trim() !== ''
    )
    updateContentWithFrontmatter(validFields, '')
    onFrontmatterChange?.(validFields)
    setShowFrontmatterModal(false)
  }

  return (
    <div
      className={cn(
        'flex flex-col h-full',
        isFullscreen && 'fixed inset-0 z-50 bg-background',
        className
      )}
    >
      <Card className="flex-1 flex flex-col">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <PenTool className="h-5 w-5" />
              {title}
            </CardTitle>
            <div className="flex items-center gap-2 mb-2">
              {/* Frontmatter Button */}
              <Dialog
                open={showFrontmatterModal}
                onOpenChange={setShowFrontmatterModal}
              >
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm" type="button">
                    <Settings className="h-4 w-4 mr-1" />
                    Properties
                    {localFrontmatterFields.length > 0 && (
                      <Badge variant="secondary" className="ml-1 text-xs">
                        {localFrontmatterFields.length}
                      </Badge>
                    )}
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Content Properties</DialogTitle>
                    <DialogDescription>
                      Add custom properties and metadata to your content using
                      frontmatter.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    {localFrontmatterFields.map((field, index) => (
                      <div
                        key={index}
                        className="grid grid-cols-12 gap-2 items-end"
                      >
                        <div className="col-span-3">
                          <Label htmlFor={`key-${index}`}>Property</Label>
                          <Input
                            id={`key-${index}`}
                            value={field.key}
                            onChange={(e) =>
                              updateFrontmatterField(index, {
                                key: e.target.value,
                              })
                            }
                            placeholder="property_name"
                          />
                        </div>
                        <div className="col-span-2">
                          <Label htmlFor={`type-${index}`}>Type</Label>
                          <select
                            id={`type-${index}`}
                            value={field.type}
                            onChange={(e) =>
                              updateFrontmatterField(index, {
                                type: e.target.value as
                                  | 'string'
                                  | 'boolean'
                                  | 'number'
                                  | 'array',
                                value:
                                  e.target.value === 'boolean'
                                    ? false
                                    : e.target.value === 'number'
                                      ? 0
                                      : '',
                              })
                            }
                            className="w-full px-3 py-2 text-sm border border-input rounded-md"
                          >
                            <option value="string">Text</option>
                            <option value="boolean">Boolean</option>
                            <option value="number">Number</option>
                            <option value="array">Array</option>
                          </select>
                        </div>
                        <div className="col-span-6">
                          <Label htmlFor={`value-${index}`}>Value</Label>
                          {field.type === 'boolean' ? (
                            <div className="flex items-center space-x-2 h-10">
                              <Switch
                                checked={Boolean(field.value)}
                                onCheckedChange={(checked) =>
                                  updateFrontmatterField(index, {
                                    value: checked,
                                  })
                                }
                              />
                              <span className="text-sm">
                                {Boolean(field.value) ? 'True' : 'False'}
                              </span>
                            </div>
                          ) : (
                            <Input
                              id={`value-${index}`}
                              type={field.type === 'number' ? 'number' : 'text'}
                              value={String(field.value)}
                              onChange={(e) =>
                                updateFrontmatterField(index, {
                                  value:
                                    field.type === 'number'
                                      ? Number(e.target.value)
                                      : e.target.value,
                                })
                              }
                              placeholder={
                                field.type === 'array'
                                  ? '["item1", "item2"]'
                                  : 'Value'
                              }
                            />
                          )}
                        </div>
                        <div className="col-span-1">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => removeFrontmatterField(index)}
                            className="h-10 w-10 p-0"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                    <Button
                      type="button"
                      variant="outline"
                      onClick={addFrontmatterField}
                      className="w-full"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add Property
                    </Button>
                  </div>
                  <DialogFooter>
                    <Button
                      variant="outline"
                      onClick={() => setShowFrontmatterModal(false)}
                    >
                      Cancel
                    </Button>
                    <Button onClick={saveFrontmatter}>Save Properties</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              {/* Mode Selection */}
              <Tabs
                value={mode}
                onValueChange={(value) => setMode(value as any)}
              >
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="edit" className="flex items-center gap-1">
                    <Edit3 className="h-3 w-3" />
                    Edit
                  </TabsTrigger>
                  <TabsTrigger
                    value="split"
                    className="flex items-center gap-1"
                  >
                    <Split className="h-3 w-3" />
                    Split
                  </TabsTrigger>
                  <TabsTrigger
                    value="preview"
                    className="flex items-center gap-1"
                  >
                    <Eye className="h-3 w-3" />
                    Preview
                  </TabsTrigger>
                </TabsList>
              </Tabs>

              {/* Fullscreen Toggle */}
              <Button
                variant="outline"
                size="sm"
                type="button"
                onClick={(e) => {
                  e.preventDefault()
                  setIsFullscreen(!isFullscreen)
                }}
              >
                {isFullscreen ? (
                  <Minimize2 className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          {/* Content Statistics */}
          {showStats && (
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <Badge variant="secondary" className="text-xs">
                <FileText className="h-3 w-3 mr-1" />
                {stats.words} words
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {stats.characters} chars
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {stats.paragraphs} paragraphs
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {stats.readingTime} min read
              </Badge>
              {localFrontmatterFields.length > 0 && (
                <Badge variant="outline" className="text-xs">
                  <Hash className="h-3 w-3 mr-1" />
                  {localFrontmatterFields.length} properties
                </Badge>
              )}
            </div>
          )}
        </CardHeader>

        <CardContent className="flex-1 p-0">
          <div
            className="h-full min-h-[500px]"
            data-color-mode={getColorMode()}
            key={`md-editor-${getColorMode()}`} // Force re-render on theme change
          >
            <div className="wmde-markdown-var"> </div>
            <MDEditor
              value={value}
              onChange={(val) => onChange(val || '')}
              preview={getVisibleMode()}
              hideToolbar={readOnly}
              height={isFullscreen ? window.innerHeight - 200 : 500}
              textareaProps={{
                placeholder,
                style: {
                  fontSize: 16,
                  lineHeight: 1.6,
                  fontFamily:
                    'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
                },
                readOnly,
                disabled: readOnly,
              }}
              className={cn(
                'w-full',
                // Remove hardcoded colors and let the theme handle it
                '[&_.w-md-editor]:!border-border',
                '[&_.w-md-editor-text-pre]:!bg-transparent',
                '[&_.w-md-editor-text-input]:!bg-transparent',
                '[&_.w-md-editor-text-pre]:!text-foreground',
                '[&_.w-md-editor-text-input]:!text-foreground',
                '[&_.w-md-editor-text-input]:!caret-foreground',
                '[&_.w-md-editor-text-input::selection]:!bg-accent',
                '[&_.w-md-editor-text-pre_code]:!text-foreground',
                // Ensure proper focus styles
                '[&_.w-md-editor-text-input:focus]:!outline-none',
                '[&_.w-md-editor-text-input:focus]:!ring-2',
                '[&_.w-md-editor-text-input:focus]:!ring-ring'
              )}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default MarkdownEditor
