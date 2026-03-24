"use client";

import { startTransition, useEffect, useRef, useState } from "react";

import { usePathname, useRouter } from "next/navigation";
import {
  Joyride,
  type Controls,
  type EventData,
  type Step,
  type TourData,
} from "react-joyride";

import { useLocale } from "@/providers/locale-provider";

const TOUR_STORAGE_KEY = "extract-agent.onboarding-tour.v2.completed";
const TOUR_RESTART_EVENT = "extract-agent:onboarding-tour-restart";
const DEMO_DOCUMENT_NAME = "convention mandat MSH.pdf";
const DEMO_DOCUMENT_URL = encodeURI(`/${DEMO_DOCUMENT_NAME}`);
const DEMO_TEMPLATE_NAME = "Convention de mandat de maîtrise d'ouvrage";
const DEMO_CORRECTION_PROMPT =
  "The address is 11 Rue Jaufre Rudel 34080 Montpellier and the siret number ends with a 3";
const DEMO_EXPECTED_ADDRESS = "11 Rue Jaufre Rudel 34080 Montpellier";
const SHORT_WAIT_TIMEOUT_MS = 4_000;
const ROUTE_WAIT_TIMEOUT_MS = 120_000;
const LONG_RUN_TIMEOUT_MS = 300_000;
const WAITING_STEP_BUTTONS = ["skip"] as const;

function waitForCondition(
  predicate: () => boolean,
  timeoutMs = SHORT_WAIT_TIMEOUT_MS,
) {
  return new Promise<void>((resolve, reject) => {
    const startedAt = Date.now();

    function check() {
      if (predicate()) {
        resolve();
        return;
      }

      if (Date.now() - startedAt >= timeoutMs) {
        reject(new Error("Timed out while waiting for onboarding state."));
        return;
      }

      window.setTimeout(check, 75);
    }

    check();
  });
}

function setFormControlValue(
  element: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement,
  value: string,
) {
  const prototype =
    element instanceof HTMLTextAreaElement
      ? HTMLTextAreaElement.prototype
      : element instanceof HTMLSelectElement
        ? HTMLSelectElement.prototype
        : HTMLInputElement.prototype;
  const valueSetter = Object.getOwnPropertyDescriptor(prototype, "value")?.set;

  valueSetter?.call(element, value);
  element.dispatchEvent(new Event("input", { bubbles: true }));
  element.dispatchEvent(new Event("change", { bubbles: true }));
}

export function WorkspaceOnboardingTour() {
  const router = useRouter();
  const pathname = usePathname();
  const pathnameRef = useRef(pathname);
  const actionHistoryRef = useRef<Set<string>>(new Set());
  const controlsRef = useRef<Controls | null>(null);
  const { messages } = useLocale();
  const [run, setRun] = useState(false);
  const [instanceKey, setInstanceKey] = useState(0);

  useEffect(() => {
    pathnameRef.current = pathname;
  }, [pathname]);

  useEffect(() => {
    if (window.localStorage.getItem(TOUR_STORAGE_KEY) === "true") {
      return;
    }

    const timer = window.setTimeout(() => {
      actionHistoryRef.current = new Set();
      setInstanceKey((current) => current + 1);
      setRun(true);
    }, 150);

    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    function handleRestart() {
      window.localStorage.removeItem(TOUR_STORAGE_KEY);
      actionHistoryRef.current = new Set();
      setRun(false);

      window.setTimeout(() => {
        setInstanceKey((current) => current + 1);
        setRun(true);
      }, 40);
    }

    window.addEventListener(TOUR_RESTART_EVENT, handleRestart);

    return () => {
      window.removeEventListener(TOUR_RESTART_EVENT, handleRestart);
    };
  }, []);

  async function ensureRoute(route: string) {
    if (pathnameRef.current === route) {
      return;
    }

    startTransition(() => {
      router.push(route);
    });

    await waitForCondition(() => pathnameRef.current === route, ROUTE_WAIT_TIMEOUT_MS).catch(
      () => undefined,
    );
  }

  async function waitForPathMatch(
    pattern: RegExp,
    timeoutMs = ROUTE_WAIT_TIMEOUT_MS,
  ) {
    await waitForCondition(() => pattern.test(pathnameRef.current), timeoutMs).catch(
      () => undefined,
    );
  }

  async function waitForElement<T extends Element>(
    selector: string,
    timeoutMs = SHORT_WAIT_TIMEOUT_MS,
  ) {
    await waitForCondition(
      () => Boolean(document.querySelector(selector)),
      timeoutMs,
    );
    return document.querySelector<T>(selector);
  }

  function clickSelector(selector: string) {
    document.querySelector<HTMLElement>(selector)?.click();
  }

  async function prepareDemoUpload() {
    await ensureRoute("/documents");

    const input = await waitForElement<HTMLInputElement>(
      "#documents-upload-input",
      ROUTE_WAIT_TIMEOUT_MS,
    ).catch(() => null);

    if (!input) {
      return;
    }

    const response = await fetch(DEMO_DOCUMENT_URL);
    const blob = await response.blob();
    const transfer = new DataTransfer();
    transfer.items.add(
      new File([blob], DEMO_DOCUMENT_NAME, {
        type: blob.type || "application/pdf",
      }),
    );

    input.files = transfer.files;
    input.dispatchEvent(new Event("change", { bubbles: true }));

    await waitForCondition(() => {
      const button = document.querySelector<HTMLButtonElement>(
        "[data-tour='documents-upload-action']",
      );

      return Boolean(button && !button.disabled);
    }).catch(() => undefined);
  }

  async function selectTemplateByName(templateName: string) {
    const selector = "#document-processing-template";
    await waitForCondition(() => {
      const select = document.querySelector<HTMLSelectElement>(selector);
      return Boolean(
        select &&
          Array.from(select.options).some(
            (option) => option.textContent?.trim() === templateName,
          ),
      );
    }, ROUTE_WAIT_TIMEOUT_MS).catch(() => undefined);

    const select = document.querySelector<HTMLSelectElement>(selector);
    if (!select) {
      return;
    }

    const option = Array.from(select.options).find(
      (candidate) => candidate.textContent?.trim() === templateName,
    );

    if (!option) {
      return;
    }

    setFormControlValue(select, option.value);
  }

  async function waitForExtractionDraft() {
    await waitForCondition(() => {
      const siretInput = document.querySelector<HTMLInputElement>(
        "#maitre_ouvrage_siret-value",
      );
      const addressInput = document.querySelector<HTMLInputElement>(
        "#maitre_ouvrage_adresse-value",
      );

      return Boolean(siretInput && addressInput);
    }, LONG_RUN_TIMEOUT_MS).catch(() => undefined);
  }

  async function waitForSuggestionOrExtractionDraft() {
    await waitForCondition(() => {
      const suggestionAcceptButton = document.querySelector(
        "[data-tour='processing-category-suggestion-accept']",
      );
      const siretInput = document.querySelector<HTMLInputElement>(
        "#maitre_ouvrage_siret-value",
      );
      const addressInput = document.querySelector<HTMLInputElement>(
        "#maitre_ouvrage_adresse-value",
      );

      return Boolean(suggestionAcceptButton || (siretInput && addressInput));
    }, LONG_RUN_TIMEOUT_MS).catch(() => undefined);
  }

  async function fillCorrectionPrompt() {
    const textarea = await waitForElement<HTMLTextAreaElement>(
      "#extraction-correction-input",
      ROUTE_WAIT_TIMEOUT_MS,
    ).catch(() => null);

    if (!textarea) {
      return;
    }

    setFormControlValue(textarea, DEMO_CORRECTION_PROMPT);

    await waitForCondition(() => {
      const button = document.querySelector<HTMLButtonElement>(
        "[data-tour='correction-chat-send']",
      );
      return Boolean(button && !button.disabled);
    }).catch(() => undefined);
  }

  async function waitForCorrectedValues() {
    await waitForCondition(() => {
      const siretInput = document.querySelector<HTMLInputElement>(
        "#maitre_ouvrage_siret-value",
      );
      const addressInput = document.querySelector<HTMLInputElement>(
        "#maitre_ouvrage_adresse-value",
      );

      return Boolean(
        siretInput?.value.trim().endsWith("3") &&
          addressInput?.value.trim() === DEMO_EXPECTED_ADDRESS,
      );
    }, LONG_RUN_TIMEOUT_MS).catch(() => undefined);
  }

  async function waitForConfirmedExtraction() {
    await waitForCondition(() => {
      const processingPanel = document.querySelector("[data-tour='processing-panel']");
      const inlineExtraction = document.querySelector(
        "[data-tour='document-inline-extraction']",
      );

      return Boolean(!processingPanel && inlineExtraction);
    }, LONG_RUN_TIMEOUT_MS).catch(() => undefined);
  }

  function startAutoAdvance(actionId: string, task: () => Promise<void>) {
    runActionOnce(actionId, () => {
      void task();
    });
  }

  function runActionOnce(actionId: string, action: () => void) {
    if (actionHistoryRef.current.has(actionId)) {
      return;
    }

    actionHistoryRef.current.add(actionId);
    action();
  }

  function runAfterNext(actionId: string, action: () => void) {
    return (data: TourData) => {
      if (data.action !== "next") {
        return;
      }

      runActionOnce(actionId, action);
    };
  }

  function handleEvent(data: EventData, controls: Controls) {
    controlsRef.current = controls;

    if (data.type === "error:target_not_found") {
      controls.next();
      return;
    }

    if (data.status === "finished" || data.status === "skipped") {
      window.localStorage.setItem(TOUR_STORAGE_KEY, "true");
      setRun(false);
    }
  }

  const steps: Step[] = [
    {
      target: "[data-tour='workspace-overview']",
      title: messages.joyride.steps.workspace.title,
      content: messages.joyride.steps.workspace.content,
      placement: "right-start",
    },
    {
      target: "[data-tour='nav-templates']",
      title: messages.joyride.steps.templatesNav.title,
      content: messages.joyride.steps.templatesNav.content,
      placement: "right",
    },
    {
      target: "[data-tour='templates-table']",
      title: messages.joyride.steps.templatesTable.title,
      content: messages.joyride.steps.templatesTable.content,
      placement: "top",
      before: async () => ensureRoute("/extraction-templates"),
    },
    {
      target: "[data-tour='nav-categories']",
      title: messages.joyride.steps.categoriesNav.title,
      content: messages.joyride.steps.categoriesNav.content,
      placement: "right",
    },
    {
      target: "[data-tour='categories-table']",
      title: messages.joyride.steps.categoriesTable.title,
      content: messages.joyride.steps.categoriesTable.content,
      placement: "top",
      before: async () => ensureRoute("/document-categories"),
    },
    {
      target: "[data-tour='nav-documents']",
      title: messages.joyride.steps.documentsNav.title,
      content: messages.joyride.steps.documentsNav.content,
      placement: "right",
    },
    {
      target: "[data-tour='documents-upload']",
      title: messages.joyride.steps.documentsUpload.title,
      content: messages.joyride.steps.documentsUpload.content,
      placement: "top",
      before: async () => {
        await prepareDemoUpload();
      },
    },
    {
      target: "[data-tour='documents-upload-action']",
      title: messages.joyride.steps.documentsUploadAction.title,
      content: messages.joyride.steps.documentsUploadAction.content,
      placement: "left",
      before: async () => {
        await prepareDemoUpload();
      },
      after: runAfterNext("upload-demo-document", () => {
        clickSelector("[data-tour='documents-upload-action']");
      }),
    },
    {
      target: "[data-tour='document-process-action']",
      title: messages.joyride.steps.processDocument.title,
      content: messages.joyride.steps.processDocument.content,
      placement: "bottom",
      targetWaitTimeout: ROUTE_WAIT_TIMEOUT_MS,
      before: async () => {
        await waitForPathMatch(/^\/documents\/[^/]+$/);
        await waitForElement(
          "[data-tour='document-process-action']",
          ROUTE_WAIT_TIMEOUT_MS,
        ).catch(() => null);
      },
      after: runAfterNext("open-processing-panel", () => {
        clickSelector("[data-tour='document-process-action']");
      }),
    },
    {
      target: "[data-tour='processing-template-select']",
      title: messages.joyride.steps.templateSelection.title,
      content: messages.joyride.steps.templateSelection.content,
      placement: "bottom",
      before: async () => {
        await waitForElement("[data-tour='processing-panel']", ROUTE_WAIT_TIMEOUT_MS).catch(
          () => null,
        );
        await selectTemplateByName(DEMO_TEMPLATE_NAME);
      },
    },
    {
      target: "[data-tour='processing-ai-option']",
      title: messages.joyride.steps.aiClassification.title,
      content: messages.joyride.steps.aiClassification.content,
      placement: "top",
      after: runAfterNext("start-ai-classification", () => {
        clickSelector("[data-tour='processing-ai-option']");
      }),
    },
    {
      target: "[data-tour='processing-live-progress']",
      title: messages.joyride.steps.liveProcessing.title,
      content: messages.joyride.steps.liveProcessing.content,
      placement: "top",
      buttons: [...WAITING_STEP_BUTTONS],
      dismissKeyAction: false,
      overlayClickAction: false,
      blockTargetInteraction: true,
      before: async () => {
        await waitForElement("[data-tour='processing-live-progress']", ROUTE_WAIT_TIMEOUT_MS).catch(
          () => null,
        );
        startAutoAdvance("wait-for-classification-branch", async () => {
          await waitForSuggestionOrExtractionDraft();
          controlsRef.current?.next();
        });
      },
    },
    {
      target: "[data-tour='processing-category-suggestion-accept']",
      title: messages.joyride.steps.categorySuggestion.title,
      content: messages.joyride.steps.categorySuggestion.content,
      placement: "top",
      before: async () => {
        await waitForSuggestionOrExtractionDraft();
      },
      after: runAfterNext("accept-category-suggestion", () => {
        clickSelector("[data-tour='processing-category-suggestion-accept']");
      }),
    },
    {
      target: "[data-tour='processing-live-progress']",
      title: messages.joyride.steps.extractionWait.title,
      content: messages.joyride.steps.extractionWait.content,
      placement: "top",
      buttons: [...WAITING_STEP_BUTTONS],
      dismissKeyAction: false,
      overlayClickAction: false,
      blockTargetInteraction: true,
      before: async () => {
        await waitForElement("[data-tour='processing-live-progress']", ROUTE_WAIT_TIMEOUT_MS).catch(
          () => null,
        );
        startAutoAdvance("wait-for-extraction-draft", async () => {
          await waitForExtractionDraft();
          controlsRef.current?.next();
        });
      },
    },
    {
      target: "[data-tour='extraction-field-maitre_ouvrage_siret']",
      title: messages.joyride.steps.initialExtraction.title,
      content: messages.joyride.steps.initialExtraction.content,
      placement: "left",
      before: async () => {
        await waitForExtractionDraft();
      },
    },
    {
      target: "[data-tour='extraction-field-maitre_ouvrage_adresse']",
      title: messages.joyride.steps.initialAddress.title,
      content: messages.joyride.steps.initialAddress.content,
      placement: "left",
      before: async () => {
        await waitForExtractionDraft();
      },
    },
    {
      target: "[data-tour='correction-chat-input']",
      title: messages.joyride.steps.correctionPrompt.title,
      content: messages.joyride.steps.correctionPrompt.content,
      placement: "top",
      before: async () => {
        await fillCorrectionPrompt();
      },
    },
    {
      target: "[data-tour='correction-chat-send']",
      title: messages.joyride.steps.sendCorrection.title,
      content: messages.joyride.steps.sendCorrection.content,
      placement: "left",
      after: runAfterNext("send-correction-message", () => {
        clickSelector("[data-tour='correction-chat-send']");
      }),
    },
    {
      target: "[data-tour='correction-chat-conversation']",
      title: messages.joyride.steps.correctionActivity.title,
      content: messages.joyride.steps.correctionActivity.content,
      placement: "top",
      buttons: [...WAITING_STEP_BUTTONS],
      dismissKeyAction: false,
      overlayClickAction: false,
      blockTargetInteraction: true,
      before: async () => {
        await waitForElement(
          "[data-tour='correction-chat-conversation']",
          ROUTE_WAIT_TIMEOUT_MS,
        ).catch(() => null);
        startAutoAdvance("wait-for-correction-completion", async () => {
          await waitForCorrectedValues();
          controlsRef.current?.next();
        });
      },
    },
    {
      target: "[data-tour='extraction-field-maitre_ouvrage_siret']",
      title: messages.joyride.steps.correctedValues.title,
      content: messages.joyride.steps.correctedValues.content,
      placement: "left",
      before: async () => {
        await waitForCorrectedValues();
      },
    },
    {
      target: "[data-tour='extraction-field-maitre_ouvrage_adresse']",
      title: messages.joyride.steps.correctedAddress.title,
      content: messages.joyride.steps.correctedAddress.content,
      placement: "left",
      before: async () => {
        await waitForCorrectedValues();
      },
    },
    {
      target: "[data-tour='processing-review-save']",
      title: messages.joyride.steps.confirmReview.title,
      content: messages.joyride.steps.confirmReview.content,
      placement: "top",
      before: async () => {
        await waitForCorrectedValues();
      },
      after: runAfterNext("confirm-reviewed-extraction", () => {
        clickSelector("[data-tour='processing-review-save']");
      }),
    },
    {
      target: "[data-tour='document-inline-extraction']",
      title: messages.joyride.steps.finalOverview.title,
      content: messages.joyride.steps.finalOverview.content,
      placement: "top",
      before: async () => {
        await waitForConfirmedExtraction();
      },
    },
    {
      target: "[data-tour='workspace-language']",
      title: messages.joyride.steps.language.title,
      content: messages.joyride.steps.language.content,
      placement: "right",
    },
    {
      target: "[data-tour='tour-restart']",
      title: messages.joyride.steps.replay.title,
      content: messages.joyride.steps.replay.content,
      placement: "right",
    },
  ];

  return (
    <Joyride
      key={instanceKey}
      continuous
      locale={{
        back: messages.joyride.actions.back,
        close: messages.joyride.actions.close,
        last: messages.joyride.actions.finish,
        next: messages.joyride.actions.next,
        nextWithProgress: messages.joyride.actions.nextWithProgress,
        open: messages.joyride.actions.open,
        skip: messages.joyride.actions.skip,
      }}
      onEvent={handleEvent}
      options={{
        backgroundColor: "#ffffff",
        blockTargetInteraction: true,
        buttons: ["skip", "primary"],
        closeButtonAction: "skip",
        dismissKeyAction: false,
        overlayColor: "rgba(20, 27, 45, 0.56)",
        overlayClickAction: false,
        primaryColor: "#1d5bdb",
        scrollDuration: 250,
        scrollOffset: 24,
        showProgress: true,
        skipBeacon: true,
        spotlightPadding: 16,
        spotlightRadius: 28,
        targetWaitTimeout: SHORT_WAIT_TIMEOUT_MS,
        textColor: "#141b2d",
        width: 440,
        zIndex: 220,
      }}
      run={run}
      scrollToFirstStep
      steps={steps}
    />
  );
}

export { TOUR_RESTART_EVENT };
