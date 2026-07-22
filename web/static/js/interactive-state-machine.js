/**
 * JobHunt Pro - Enterprise UI Finite State Machine (FSM)
 * Handles interactive button states, async fetch calls, anti-double-click, and automatic feedback UI.
 * WCAG 2.1 AAA & Hardware Acceleration Compliant.
 */

(function (window, document) {
  'use strict';

  class UIStateMachine {
    constructor(element, options = {}) {
      this.element = typeof element === 'string' ? document.querySelector(element) : element;
      if (!this.element) return;

      this.options = Object.assign({
        loadingText: 'جاري المعالجة...',
        successText: 'تمت العملية بنجاح ✓',
        errorText: 'حدث خطأ، أعد المحاولة',
        resetDelay: 2500,
        onSuccess: null,
        onError: null
      }, options);

      this.state = 'idle'; // idle | loading | success | error | disabled
      this.originalContent = this.element.innerHTML;
      this.originalBackground = this.element.style.background;
      this.originalColor = this.element.style.color;

      this._init();
    }

    _init() {
      this.element.setAttribute('data-fsm-state', 'idle');
      this.element.classList.add('fsm-btn-ready');
    }

    setState(newState, customMessage = null) {
      this.state = newState;
      this.element.setAttribute('data-fsm-state', newState);

      switch (newState) {
        case 'loading':
          this.element.disabled = true;
          this.element.innerHTML = `
            <span class="fsm-spinner" aria-hidden="true"></span>
            <span>${customMessage || this.options.loadingText}</span>
          `;
          break;

        case 'success':
          this.element.disabled = true;
          this.element.classList.add('fsm-state-success');
          this.element.innerHTML = `
            <span class="fsm-icon-success">✓</span>
            <span>${customMessage || this.options.successText}</span>
          `;
          if (typeof this.options.onSuccess === 'function') this.options.onSuccess();
          this._scheduleReset();
          break;

        case 'error':
          this.element.disabled = false;
          this.element.classList.add('fsm-state-error');
          this.element.innerHTML = `
            <span class="fsm-icon-error">⚠</span>
            <span>${customMessage || this.options.errorText}</span>
          `;
          if (typeof this.options.onError === 'function') this.options.onError();
          this._scheduleReset();
          break;

        case 'idle':
        default:
          this.element.disabled = false;
          this.element.classList.remove('fsm-state-success', 'fsm-state-error');
          this.element.innerHTML = this.originalContent;
          break;
      }
    }

    _scheduleReset() {
      setTimeout(() => {
        if (this.state === 'success' || this.state === 'error') {
          this.setState('idle');
        }
      }, this.options.resetDelay);
    }

    async execute(asyncCallback, loadingMessage = null) {
      if (this.state === 'loading') return;
      this.setState('loading', loadingMessage);
      try {
        const result = await asyncCallback();
        this.setState('success');
        return result;
      } catch (err) {
        console.error('[FSM Error]', err);
        this.setState('error', err.message || this.options.errorText);
        throw err;
      }
    }
  }

  // Global Attach
  window.UIStateMachine = UIStateMachine;

  // Auto Bind Data Attribute Elements
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-fsm-action]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const actionUrl = btn.getAttribute('data-fsm-action');
        const method = btn.getAttribute('data-fsm-method') || 'POST';
        const fsm = new UIStateMachine(btn);

        await fsm.execute(async () => {
          const response = await fetch(actionUrl, {
            method: method,
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest'
            }
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || 'فشل الاتصال بالخادم');
          }

          return await response.json();
        });
      });
    });
  });
})(window, document);
