/**
 * Glass-Note Tooltip Module
 * Apple-style translucent tooltips for French vocabulary words
 */

(() => {
    'use strict';

    class GlassNoteTooltip {
        constructor() {
            this.currentTip = null;
            this.currentTrigger = null;
            this.touchTimer = null;
            this.isMobile = window.innerWidth <= 480;
            
            this.init();
        }

        init() {
            this.setupEventListeners();
            this.handleResize();
        }

        setupEventListeners() {
            // Global event listeners
            document.addEventListener('click', this.handleDocumentClick.bind(this));
            document.addEventListener('keydown', this.handleKeydown.bind(this));
            window.addEventListener('resize', this.handleResize.bind(this));
            
            // Set up triggers when DOM changes
            this.setupTriggers();
            
            // Observer for dynamically added content
            const observer = new MutationObserver(() => {
                this.setupTriggers();
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }

        setupTriggers() {
            const triggers = document.querySelectorAll('.french-word');
            
            triggers.forEach(trigger => {
                // Skip if already set up
                if (trigger.dataset.tooltipSetup) return;
                
                // Mark as set up
                trigger.dataset.tooltipSetup = 'true';
                
                // Add accessibility attributes
                this.setupTriggerAccessibility(trigger);
                
                // Add event listeners
                this.addTriggerEvents(trigger);
            });
        }

        setupTriggerAccessibility(trigger) {
            // Ensure tabindex for keyboard navigation
            if (!trigger.hasAttribute('tabindex')) {
                trigger.setAttribute('tabindex', '0');
            }
            
            // Generate unique ID for tooltip
            const tooltipId = `tooltip-${Math.random().toString(36).substr(2, 9)}`;
            trigger.setAttribute('aria-describedby', tooltipId);
            trigger.setAttribute('aria-expanded', 'false');
            
            // Store tooltip ID
            trigger.dataset.tooltipId = tooltipId;
        }

        addTriggerEvents(trigger) {
            // Mouse events (desktop)
            trigger.addEventListener('mouseenter', (e) => this.handleMouseEnter(e));
            trigger.addEventListener('mouseleave', (e) => this.handleMouseLeave(e));
            
            // Focus events (keyboard navigation)
            trigger.addEventListener('focus', (e) => this.handleFocus(e));
            trigger.addEventListener('blur', (e) => this.handleBlur(e));
            
            // Click events
            trigger.addEventListener('click', (e) => this.handleClick(e));
            
            // Touch events (mobile)
            trigger.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
            trigger.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: true });
            trigger.addEventListener('touchcancel', (e) => this.handleTouchCancel(e), { passive: true });
        }

        handleMouseEnter(e) {
            if (this.isMobile) return;
            this.showTooltip(e.target);
        }

        handleMouseLeave(e) {
            if (this.isMobile) return;
            this.hideTooltip();
        }

        handleFocus(e) {
            if (this.isMobile) return;
            this.showTooltip(e.target);
        }

        handleBlur(e) {
            if (this.isMobile) return;
            // Small delay to allow for tooltip interaction
            setTimeout(() => {
                if (this.currentTip && !this.currentTip.matches(':hover, :focus-within')) {
                    this.hideTooltip();
                }
            }, 100);
        }

        handleClick(e) {
            e.preventDefault();
            
            if (this.currentTrigger === e.target && this.currentTip) {
                this.hideTooltip();
            } else {
                this.showTooltip(e.target);
            }
        }

        handleTouchStart(e) {
            const trigger = e.target;
            
            // Immediate tooltip show on touch (no long press needed)
            this.showTooltip(trigger);
            this.vibrate();
        }

        handleTouchEnd(e) {
            // No timer to clear anymore - keeping for future use
        }

        handleTouchCancel(e) {
            // No timer to clear anymore - keeping for future use
        }

        handleDocumentClick(e) {
            // Close tooltip when clicking outside or on the tooltip itself
            if (this.currentTip && !this.currentTrigger.contains(e.target)) {
                this.hideTooltip();
            }
        }

        handleKeydown(e) {
            // ESC key closes tooltip
            if (e.key === 'Escape' && this.currentTip) {
                this.hideTooltip();
                
                // Return focus to trigger
                if (this.currentTrigger) {
                    this.currentTrigger.focus();
                }
            }
            
            // Enter/Space on trigger shows tooltip
            if ((e.key === 'Enter' || e.key === ' ') && 
                e.target.classList.contains('french-word')) {
                e.preventDefault();
                
                if (this.currentTrigger === e.target && this.currentTip) {
                    this.hideTooltip();
                } else {
                    this.showTooltip(e.target);
                }
            }
        }

        handleResize() {
            const wasMobile = this.isMobile;
            this.isMobile = window.innerWidth <= 480;
            
            // If switching between mobile/desktop, hide current tooltip
            if (wasMobile !== this.isMobile && this.currentTip) {
                this.hideTooltip();
            }
        }

        showTooltip(trigger) {
            // Hide any existing tooltip
            this.hideTooltip();
            
            // Extract data from trigger
            const data = this.extractTooltipData(trigger);
            if (!data) return;
            
            // Build tooltip
            const tooltip = this.buildTooltip(trigger, data);
            
            // Add to DOM
            document.body.appendChild(tooltip);
            
            // Position tooltip
            this.positionTooltip(trigger, tooltip);
            
            // Show with animation
            requestAnimationFrame(() => {
                tooltip.classList.add('visible');
            });
            
            // Update state
            this.currentTip = tooltip;
            this.currentTrigger = trigger;
            
            // Update accessibility
            trigger.setAttribute('aria-expanded', 'true');
            
            // Vibrate on mobile
            if (this.isMobile) {
                this.vibrate();
            }
        }

        hideTooltip() {
            if (!this.currentTip) return;
            
            const tooltip = this.currentTip;
            const trigger = this.currentTrigger;
            
            // Hide with animation
            tooltip.classList.remove('visible');
            
            // Update accessibility
            if (trigger) {
                trigger.setAttribute('aria-expanded', 'false');
            }
            
            // Remove from DOM after animation
            setTimeout(() => {
                if (tooltip.parentNode) {
                    tooltip.parentNode.removeChild(tooltip);
                }
            }, 200);
            
            // Clear state
            this.currentTip = null;
            this.currentTrigger = null;
        }

        extractTooltipData(trigger) {
            try {
                // Data is stored as JSON in the data-word attribute
                const dataString = trigger.getAttribute('data-word');
                if (!dataString) return null;
                
                const data = JSON.parse(decodeURIComponent(dataString));
                
                // Extract display text from display_format (remove markdown formatting)
                let displayText = data.display_format || data.original_word || trigger.textContent;
                
                // Clean up display_format - remove markdown bold formatting and extract main term
                if (data.display_format) {
                    // Remove **text:** pattern and get the text before the colon
                    const match = displayText.match(/\*\*([^:*]+)[:\*]/);
                    if (match) {
                        displayText = match[1].trim();
                    } else {
                        // Fallback: remove all markdown formatting
                        displayText = displayText.replace(/\*\*/g, '').split(':')[0].trim();
                    }
                }
                
                return {
                    word: data.original_word || trigger.textContent,
                    display: displayText,
                    explanation: data.explanation || data.english_translation || '',
                    note: data.cultural_note || data.linguistic_note || ''
                };
            } catch (error) {
                console.warn('Failed to parse tooltip data:', error);
                
                // Fallback to basic display
                return {
                    word: trigger.textContent,
                    display: trigger.textContent,
                    explanation: 'Translation not available',
                    note: ''
                };
            }
        }

        buildTooltip(trigger, data) {
            const tooltip = document.createElement('div');
            tooltip.className = 'glass-note-tooltip';
            tooltip.setAttribute('role', 'tooltip');
            tooltip.setAttribute('id', trigger.dataset.tooltipId);
            
            // Add click handler to close tooltip when tapped
            tooltip.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent event bubbling
                this.hideTooltip();
            });
            
            // Build content
            let content = `<strong class="word-display">${this.escapeHtml(data.display)}</strong>`;
            
            if (data.explanation) {
                content += `<p class="definition">${this.escapeHtml(data.explanation)}</p>`;
            }
            
            if (data.note) {
                content += `<p class="note">${this.escapeHtml(data.note)}</p>`;
            }
            
            tooltip.innerHTML = content;
            
            // Check if content is tall on mobile
            if (this.isMobile) {
                // Temporarily add to DOM to measure
                tooltip.style.visibility = 'hidden';
                tooltip.style.position = 'fixed';
                tooltip.style.bottom = '0';
                document.body.appendChild(tooltip);
                
                const height = tooltip.offsetHeight;
                const viewportHeight = window.innerHeight;
                
                if (height > viewportHeight * 0.4) {
                    tooltip.classList.add('tall-content');
                }
                
                document.body.removeChild(tooltip);
                tooltip.style.visibility = '';
                tooltip.style.position = '';
            }
            
            return tooltip;
        }

        positionTooltip(trigger, tooltip) {
            if (this.isMobile) {
                // Mobile uses fixed bottom positioning
                return;
            }
            
            const triggerRect = trigger.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            const scrollTop = window.pageYOffset;
            const scrollLeft = window.pageXOffset;
            
            let placement = 'bottom'; // Default to bottom (tooltip above trigger)
            let left = triggerRect.left + scrollLeft + (triggerRect.width / 2) - (tooltipRect.width / 2);
            let top = triggerRect.top + scrollTop - tooltipRect.height - 12; // 12px gap
            
            // Check if tooltip fits above trigger
            if (top < scrollTop + 16) {
                // Not enough space above, place below
                placement = 'top';
                top = triggerRect.bottom + scrollTop + 12;
            }
            
            // Clamp horizontal position within viewport with 16px padding
            const minLeft = scrollLeft + 16;
            const maxLeft = scrollLeft + viewportWidth - tooltipRect.width - 16;
            left = Math.max(minLeft, Math.min(maxLeft, left));
            
            // Apply positioning
            tooltip.style.left = `${left}px`;
            tooltip.style.top = `${top}px`;
            tooltip.classList.add(`placement-${placement}`);
        }

        vibrate() {
            if ('vibrate' in navigator) {
                navigator.vibrate(8);
            }
        }

        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            new GlassNoteTooltip();
        });
    } else {
        new GlassNoteTooltip();
    }

})(); 