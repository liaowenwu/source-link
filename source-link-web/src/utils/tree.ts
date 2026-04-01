import type { TreeOption } from 'naive-ui'
import type { TreeOptionNode } from '@/types/common'

export function toNaiveTreeOptions(nodes: TreeOptionNode[] = []): TreeOption[] {
  return nodes.map((node) => ({
    key: node.id,
    label: node.label,
    disabled: node.disabled,
    children: node.children ? toNaiveTreeOptions(node.children) : undefined,
  }))
}

export function flattenTree<T extends { children?: T[] }>(nodes: T[] = []): T[] {
  return nodes.flatMap((node) => [node, ...flattenTree(node.children ?? [])])
}
