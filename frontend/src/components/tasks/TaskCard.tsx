"use client";

import type { TaskResponse } from "@/lib/types/api";

interface TaskCardProps {
  task: TaskResponse;
  onEdit: (task: TaskResponse) => void;
  onDelete: (task: TaskResponse) => void;
  onViewDetails: (task: TaskResponse) => void;
}

const STATUS_COLORS = {
  TODO: "bg-gray-100 text-gray-800",
  IN_PROGRESS: "bg-blue-100 text-blue-800",
  DONE: "bg-green-100 text-green-800",
  BLOCKED: "bg-red-100 text-red-800",
};

const PRIORITY_COLORS = {
  LOW: "bg-gray-100 text-gray-600",
  MEDIUM: "bg-yellow-100 text-yellow-800",
  HIGH: "bg-red-100 text-red-800",
  CRITICAL: "bg-purple-100 text-purple-800",
};

const STATUS_LABELS = {
  TODO: "To Do",
  IN_PROGRESS: "In Progress",
  DONE: "Done",
  BLOCKED: "Blocked",
};

export function TaskCard({ task, onEdit, onDelete, onViewDetails }: TaskCardProps) {
  const formatDate = (date: string) => {
    const d = new Date(date);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== "DONE";

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 hover:shadow-sm transition">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-mono font-semibold ${STATUS_COLORS[task.status] || STATUS_COLORS.TODO
              }`}
          >
            {STATUS_LABELS[task.status] || task.status}
          </span>
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-mono font-semibold ${PRIORITY_COLORS[task.priority] || PRIORITY_COLORS.MEDIUM
              }`}
          >
            {task.priority}
          </span>
        </div>
        <div className="text-xs text-gray-500">
          {task.due_date ? (
            <span className={isOverdue ? "text-rose-600 font-semibold" : ""}>
              Due {formatDate(task.due_date)}
            </span>
          ) : (
            <span className="text-gray-400">No due date</span>
          )}
        </div>
      </div>

      <button
        className="text-left w-full mt-3"
        onClick={() => onViewDetails(task)}
        title={task.title}
      >
        <h3 className="text-lg font-semibold text-gray-900 leading-tight hover:text-indigo-600">
          {task.title}
        </h3>
        {task.description && (
          <p className="mt-1 text-sm text-gray-600 line-clamp-2">{task.description}</p>
        )}
      </button>

      {task.tags && task.tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {task.tags.slice(0, 4).map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-gray-100 text-gray-700"
            >
              #{tag}
            </span>
          ))}
          {task.tags.length > 4 && (
            <span className="text-[11px] text-gray-500 font-semibold">+{task.tags.length - 4}</span>
          )}
        </div>
      )}

      <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onViewDetails(task)}
            className="font-semibold text-indigo-700 hover:text-indigo-900"
          >
            View
          </button>
          <button
            onClick={() => onEdit(task)}
            className="font-semibold text-gray-700 hover:text-gray-900"
          >
            Edit
          </button>
          <button
            onClick={() => onDelete(task)}
            className="font-semibold text-rose-700 hover:text-rose-900"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
