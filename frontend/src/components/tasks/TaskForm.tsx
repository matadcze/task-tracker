"use client";

import { useState } from "react";
import type { TaskCreate, TaskUpdate, TaskResponse } from "@/lib/types/api";
import { getFriendlyErrorMessage } from "@/lib/utils/error";

interface TaskFormProps {
  task?: TaskResponse;
  onSubmit: (data: TaskCreate | TaskUpdate) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

const STATUS_OPTIONS = [
  { value: "TODO", label: "To Do" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "DONE", label: "Done" },
];

const PRIORITY_OPTIONS = [
  { value: "LOW", label: "Low" },
  { value: "MEDIUM", label: "Medium" },
  { value: "HIGH", label: "High" },
];

export function TaskForm({ task, onSubmit, onCancel, isLoading }: TaskFormProps) {
  const [formData, setFormData] = useState({
    title: task?.title || "",
    description: task?.description || "",
    status: task?.status || "TODO",
    priority: task?.priority || "MEDIUM",
    due_date: task?.due_date ? new Date(task.due_date).toISOString().slice(0, 10) : "",
    tags: task?.tags?.join(", ") || "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState("");

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = "Title is required";
    } else if (formData.title.length > 500) {
      newErrors.title = "Title must be 500 characters or less";
    }

    if (formData.due_date) {
      const dueDate = new Date(formData.due_date);
      if (isNaN(dueDate.getTime())) {
        newErrors.due_date = "Invalid date format";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError("");

    if (!validate()) {
      return;
    }

    const data: TaskCreate | TaskUpdate = {
      title: formData.title.trim(),
      description: formData.description.trim() || undefined,
      status: formData.status as any,
      priority: formData.priority as any,
      due_date: formData.due_date || undefined,
      tags: formData.tags
        .split(",")
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0),
    };

    try {
      await onSubmit(data);
    } catch (err) {
      setSubmitError(getFriendlyErrorMessage(err, "Unable to save task. Please try again."));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {submitError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {submitError}
        </div>
      )}
      <div className="rounded-xl border border-indigo-50 bg-indigo-50/70 p-4">
        <p className="text-xs uppercase tracking-[0.3em] text-indigo-600 font-semibold">
          {task ? "Edit task" : "Create task"}
        </p>
        <h3 className="text-xl font-ultra-bold text-gray-900 tracking-tight">
          {task ? "Update the details" : "Craft a new task"}
        </h3>
        <p className="text-sm text-indigo-900/80 mt-1">
          Add the essentials so your future self knows exactly what to do.
        </p>
      </div>

      <div className="space-y-4">
        <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-gray-800">Basics</p>
            <span className="text-xs px-2 py-1 rounded-full bg-indigo-50 text-indigo-700 font-semibold">
              Required
            </span>
          </div>

          <div className="mt-3 space-y-3">
            <label className="block text-sm font-semibold text-gray-800">
              Title <span className="text-red-500">*</span>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className={`mt-2 block w-full rounded-md border px-3 py-2 shadow-sm sm:text-sm text-gray-900 ${
                  errors.title
                    ? "border-red-300 focus:border-red-500 focus:ring-red-500"
                    : "border-gray-300 focus:border-indigo-500 focus:ring-indigo-500"
                }`}
                placeholder="Design review, plan sprint, fix customer bug..."
                maxLength={500}
              />
            </label>
            {errors.title && <p className="text-sm text-red-600">{errors.title}</p>}

            <label className="block text-sm font-semibold text-gray-800">
              Description
              <textarea
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="mt-2 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm text-gray-900"
                placeholder="Add context, acceptance criteria, or links (optional)"
              />
            </label>
          </div>
        </div>

        <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
          <p className="text-sm font-semibold text-gray-800">Planning</p>
          <p className="text-xs text-gray-500">Set status, priority, and a target date.</p>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className="block text-sm font-semibold text-gray-800">
              Status
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="mt-2 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm text-gray-900"
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm font-semibold text-gray-800">
              Priority
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="mt-2 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm text-gray-900"
              >
                {PRIORITY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm font-semibold text-gray-800">
              Due date
              <input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className={`mt-2 block w-full rounded-md border px-3 py-2 shadow-sm sm:text-sm text-gray-900 ${
                  errors.due_date
                    ? "border-red-300 focus:border-red-500 focus:ring-red-500"
                    : "border-gray-300 focus:border-indigo-500 focus:ring-indigo-500"
                }`}
              />
              {errors.due_date && <p className="mt-1 text-sm text-red-600">{errors.due_date}</p>}
            </label>
          </div>
        </div>

        <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
          <p className="text-sm font-semibold text-gray-800">Tags</p>
          <p className="text-xs text-gray-500">Label work to filter and sort faster.</p>

          <label className="mt-3 block text-sm font-semibold text-gray-800">
            Comma-separated tags
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              className="mt-2 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm text-gray-900"
              placeholder="e.g., roadmap, quick win, customer"
            />
          </label>
          <p className="mt-1 text-xs text-gray-500">Separate multiple tags with commas.</p>
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-4 py-2 text-sm font-bold text-gray-700 bg-white border border-gray-200 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-60"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400"
        >
          {isLoading ? "Saving..." : task ? "Update Task" : "Create Task"}
        </button>
      </div>
    </form>
  );
}
