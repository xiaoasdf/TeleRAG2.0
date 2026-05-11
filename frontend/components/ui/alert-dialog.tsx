"use client";

import * as React from "react";
import * as AlertDialogPrimitive from "@radix-ui/react-alert-dialog";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const AlertDialog = AlertDialogPrimitive.Root;
export const AlertDialogTrigger = AlertDialogPrimitive.Trigger;

export function AlertDialogContent({ className, ...props }: AlertDialogPrimitive.AlertDialogContentProps) {
  return (
    <AlertDialogPrimitive.Portal>
      <AlertDialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50" />
      <AlertDialogPrimitive.Content
        className={cn(
          "fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-[1.5rem] border border-border bg-card p-6 shadow-paper",
          className
        )}
        {...props}
      />
    </AlertDialogPrimitive.Portal>
  );
}

export function AlertDialogHeader(props: React.HTMLAttributes<HTMLDivElement>) {
  return <div className="flex flex-col space-y-2 text-left" {...props} />;
}

export function AlertDialogFooter(props: React.HTMLAttributes<HTMLDivElement>) {
  return <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end" {...props} />;
}

export function AlertDialogTitle(props: AlertDialogPrimitive.AlertDialogTitleProps) {
  return <AlertDialogPrimitive.Title className="text-lg font-semibold" {...props} />;
}

export function AlertDialogDescription(props: AlertDialogPrimitive.AlertDialogDescriptionProps) {
  return <AlertDialogPrimitive.Description className="text-sm text-muted" {...props} />;
}

export function AlertDialogConfirm(props: AlertDialogPrimitive.AlertDialogActionProps) {
  return <AlertDialogPrimitive.Action className={buttonVariants({ variant: "destructive" })} {...props} />;
}

export function AlertDialogDismiss(props: AlertDialogPrimitive.AlertDialogCancelProps) {
  return <AlertDialogPrimitive.Cancel className={buttonVariants({ variant: "secondary" })} {...props} />;
}
