"use client";

import type { TaskDetailResponse } from "@/lib/types/api";
import { AttachmentManager } from "@/components/attachments/AttachmentManager";

interface TaskDetailsProps {
  taskDetail: TaskDetailResponse;
  onEdit: () => void;
  onDelete: () => void;
  onRefresh: () => void;
}

const STATUS_LABELS = {
  TODO: "To Do",
  IN_PROGRESS: "In Progress",
  DONE: "Done",
  BLOCKED: "Blocked",
};

export function TaskDetails({ taskDetail, onEdit, onDelete, onRefresh }: TaskDetailsProps) {
  const { task, attachments } = taskDetail;

  const formatDate = (date: string) => {
    return new Date(date).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start gap-4">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.25em] text-indigo-500 font-semibold">Task</p>
          <h3 className="text-2xl font-ultra-bold text-gray-900 leading-tight">{task.title}</h3>
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-gray-100 text-gray-800">
              {STATUS_LABELS[task.status] || task.status}
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-indigo-50 text-indigo-700">
              {task.priority}
            </span>
            {task.due_date && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700">
                Due {formatDate(task.due_date)}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onEdit}
            className="px-3 py-1.5 text-sm font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-md"
          >
            Edit
          </button>
          <button
            onClick={onDelete}
            className="px-3 py-1.5 text-sm font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 rounded-md"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div className="rounded-lg border border-gray-100 bg-white p-3">
          <p className="text-xs uppercase tracking-[0.2em] text-gray-500 font-semibold">Status</p>
          <p className="mt-1 text-gray-900 font-semibold">{STATUS_LABELS[task.status] || task.status}</p>
        </div>
        <div className="rounded-lg border border-gray-100 bg-white p-3">
          <p className="text-xs uppercase tracking-[0.2em] text-gray-500 font-semibold">Priority</p>
          <p className="mt-1 text-gray-900 font-semibold">{task.priority}</p>
        </div>
        <div className="rounded-lg border border-gray-100 bg-white p-3">
          <p className="text-xs uppercase tracking-[0.2em] text-gray-500 font-semibold">Created</p>
          <p className="mt-1 text-gray-900">{formatDate(task.created_at)}</p>
        </div>
        <div className="rounded-lg border border-gray-100 bg-white p-3">
          <p className="text-xs uppercase tracking-[0.2em] text-gray-500 font-semibold">Due date</p>
          <p className="mt-1 text-gray-900">
            {task.due_date ? formatDate(task.due_date) : "No due date"}
          </p>
        </div>
      </div>

      {task.description && (
        <div className="rounded-lg border border-gray-100 bg-white p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-gray-500 font-semibold">Description</p>
          <p className="mt-2 text-gray-700 whitespace-pre-wrap leading-relaxed">{task.description}</p>
        </div>
      )}

      {task.tags && task.tags.length > 0 && (
        <div className="rounded-lg border border-gray-100 bg-white p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-gray-500 font-semibold">Tags</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {task.tags.map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-gray-100 text-gray-700"
              >
                #{tag}
              </span>
            ))}
          </div>
        </div>
      )}

      <AttachmentManager taskId={task.id} attachments={attachments} onRefresh={onRefresh} />
    </div>
  );
}
