import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { JsonViewer } from '@/components/ui/json-viewer'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DBRecordInstance } from '@rushdb/javascript-sdk'
import { useRecordRelations } from '@/hooks/use-record-relations'
import { useLabelColors } from '@/hooks/use-label-colors'
import { Label } from '@/components/labels/label'
import { RelationshipGraph } from '@/components/relationship-graph'
import {
  Loader,
  Calendar,
  Database,
  Hash,
  Link2,
  FileText,
  Copy,
} from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface RecordModalProps {
  record: DBRecordInstance
  isOpen: boolean
  onClose: () => void
}

export function RecordModal({ record, isOpen, onClose }: RecordModalProps) {
  const { data: relations, isLoading } = useRecordRelations(record.id())
  const { getLabelColor } = useLabelColors()

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl h-[90vh] p-0 gap-0 bg-background border border-border flex flex-col">
        {/* Header */}
        <div className="border-b border-border bg-muted p-6 flex-shrink-0">
          <div className="flex flex-col space-y-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <Label
                  variant={getLabelColor(record.label()) as any}
                  active={true}
                  className="text-sm"
                >
                  {record.label()}
                </Label>
                <Badge variant="secondary" className="font-mono text-xs">
                  <Hash className="w-3 h-3 mr-1" />
                  {record.id().slice(-8)}
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(record.id())}
                  className="h-7 px-2 text-xs"
                >
                  <Copy className="w-3 h-3 mr-1" />
                  Copy ID
                </Button>
              </div>
            </div>
            <div>
              <DialogTitle className="text-2xl font-semibold text-foreground mb-1">
                Record Details
              </DialogTitle>
              <DialogDescription className="text-muted-foreground flex items-center gap-2">
                <Database className="w-4 h-4" />
                Full record information and relationships
              </DialogDescription>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full">
            <div className="p-6 space-y-6">
              {/* Metadata Section */}
              <Card className="border-border shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary" />
                    Metadata
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-muted-foreground">
                        Record ID
                      </div>
                      <div className="font-mono text-sm bg-muted rounded px-2 py-1 border border-border">
                        {record.id()}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-muted-foreground">
                        Created Date
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <Calendar className="w-4 h-4 text-muted-foreground" />
                        {new Date(record.date()).toLocaleDateString('en-US', {
                          weekday: 'long',
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Record Data Section */}
              <Card className="border-border shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Database className="w-5 h-5 text-amber-500" />
                    Record Data
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-muted rounded-lg border border-border p-4">
                    <JsonViewer data={record.data} />
                  </div>
                </CardContent>
              </Card>

              {/* Relationship Graph Section */}
              <div className="h-[500px]">
                <RelationshipGraph
                  record={record}
                  relations={relations}
                  isLoading={isLoading}
                />
              </div>

              {/* Relationships Section */}
              <Card className="border-border shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Link2 className="w-5 h-5 text-green-500" />
                    Relationships (Raw Data)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {isLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader className="w-6 h-6 animate-spin text-muted-foreground" />
                      <span className="ml-2 text-muted-foreground">
                        Loading relationships...
                      </span>
                    </div>
                  ) : (
                    <div className="bg-muted rounded-lg border border-border p-4">
                      <JsonViewer data={relations} />
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </ScrollArea>
        </div>

        {/* Footer */}
        <div className="border-t border-border bg-muted p-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground">
              Use the JSON viewers above to explore the complete record
              structure
            </div>
            <Button variant="outline" onClick={onClose} className="ml-auto">
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
