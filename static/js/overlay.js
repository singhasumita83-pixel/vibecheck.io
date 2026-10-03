// VibeCheck UI — Overlay and Marker Management (DESIGN V2: Red Pen)

export class OverlayManager {
  constructor(containerEl, imgEl) {
    this.container = containerEl;
    this.img = imgEl;
    this.markers = [];
    this.activeId = null;
    this.onSelectCallback = null;
  }

  onSelect(callback) {
    this.onSelectCallback = callback;
  }

  render(findings) {
    this.clear();

    // Bounding box element
    this.boxEl = document.createElement('div');
    this.boxEl.className = 'bounding-box';
    this.boxEl.style.display = 'none';
    this.container.appendChild(this.boxEl);

    // Check reduced motion preference
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    findings.forEach((finding, index) => {
      const pin = document.createElement('div');
      pin.className = 'marker-pin';
      pin.dataset.id = finding.id;
      pin.dataset.sev = finding.severity;
      pin.textContent = (index + 1).toString();
      pin.style.left = `${finding.location.x * 100}%`;
      pin.style.top = `${finding.location.y * 100}%`;
      pin.setAttribute('role', 'button');
      pin.setAttribute('tabindex', '0');
      pin.setAttribute('aria-label', `Issue ${index + 1}, ${finding.severity}: ${finding.title}`);

      // Stamp-in animation (staggered 60ms)
      if (!prefersReduced) {
        pin.style.opacity = '0';
        pin.style.transform = 'translate(-50%, -50%) scale(1.4) rotate(-8deg)';
        setTimeout(() => {
          pin.classList.add('stamp-in');
          pin.style.opacity = '';
          pin.style.transform = '';
        }, index * 60);
      }

      // Click
      pin.addEventListener('click', (e) => {
        e.stopPropagation();
        this.select(finding.id);
        if (this.onSelectCallback) this.onSelectCallback(finding.id, true);
      });

      // Hover
      pin.addEventListener('mouseenter', () => {
        this.showBoundingBox(finding.location);
      });

      pin.addEventListener('mouseleave', () => {
        if (this.activeId !== finding.id) {
          this.hideBoundingBox();
        } else {
          const activeFinding = this.markers.find(m => m.id === this.activeId);
          if (activeFinding) this.showBoundingBox(activeFinding.finding.location);
        }
      });

      // Keyboard
      pin.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.select(finding.id);
          if (this.onSelectCallback) this.onSelectCallback(finding.id, true);
        }
      });

      this.container.appendChild(pin);
      this.markers.push({ id: finding.id, el: pin, finding });
    });
  }

  select(id) {
    this.activeId = id;
    this.markers.forEach(({ id: mId, el, finding }) => {
      if (mId === id) {
        el.classList.add('active');
        this.showBoundingBox(finding.location);
      } else {
        el.classList.remove('active');
      }
    });
  }

  pulse(id) {
    this.select(id);
  }

  showBoundingBox(loc) {
    if (!this.boxEl) return;
    this.boxEl.style.display = 'block';
    this.boxEl.style.left = `${loc.x * 100}%`;
    this.boxEl.style.top = `${loc.y * 100}%`;
    this.boxEl.style.width = `${Math.max(loc.w * 100, 3)}%`;
    this.boxEl.style.height = `${Math.max(loc.h * 100, 3)}%`;
  }

  hideBoundingBox() {
    if (this.boxEl && !this.activeId) {
      this.boxEl.style.display = 'none';
    }
  }

  clear() {
    this.markers.forEach(m => m.el.remove());
    this.markers = [];
    if (this.boxEl) {
      this.boxEl.remove();
      this.boxEl = null;
    }
    this.activeId = null;
  }
}
