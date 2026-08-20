const DEFAULT_COLOR = [255, 102, 0];
const MAX_LINE_COUNT = 20;
const MIN_LINE_COUNT = 1;
const MIN_SPEED = 1;

/**
 * Moving border point used by the canvas animation.
 */
class EdgePoint {
  /** Store a point's position and inward movement vector. */
  constructor(side, xPosition, yPosition, angleDegrees, offset) {
    this.side = side;
    this.xPosition = xPosition;
    this.yPosition = yPosition;
    this.angleDegrees = angleDegrees;
    this.offset = offset;
  }

  /** Return the point as bounded integer canvas coordinates. */
  toXY(width, height) {
    return [
      Math.max(0, Math.min(width - 1, Math.round(this.xPosition))),
      Math.max(0, Math.min(height - 1, Math.round(this.yPosition))),
    ];
  }

  /** Advance the point and choose a new inward vector after an edge hit. */
  moved(width, height, offsetMinimum, offsetMaximum) {
    const angle = (this.angleDegrees * Math.PI) / 180;
    let deltaX = Math.cos(angle) * this.offset;
    let deltaY = Math.sin(angle) * this.offset;

    if (this.side === "right") {
      deltaX *= -1;
    }
    if (this.side === "top") {
      deltaY = Math.abs(deltaY);
    }
    if (this.side === "bottom") {
      deltaY = -Math.abs(deltaY);
    }
    if (this.side === "left") {
      deltaX = Math.abs(deltaX);
    }

    const nextX = this.xPosition + deltaX;
    const nextY = this.yPosition + deltaY;
    const hitSide = hitSideFor(nextX, nextY, width, height);

    if (!hitSide) {
      return new EdgePoint(this.side, nextX, nextY, this.angleDegrees, this.offset);
    }

    return new EdgePoint(
      hitSide,
      Math.max(0, Math.min(width - 1, nextX)),
      Math.max(0, Math.min(height - 1, nextY)),
      randomInt(15, 165),
      randomInt(offsetMinimum, offsetMaximum),
    );
  }
}

/**
 * Return the edge hit by a point after movement, if any.
 */
function hitSideFor(xPosition, yPosition, width, height) {
  if (xPosition <= 0) {
    return "left";
  }
  if (xPosition >= width - 1) {
    return "right";
  }
  if (yPosition <= 0) {
    return "top";
  }
  if (yPosition >= height - 1) {
    return "bottom";
  }
  return null;
}

/**
 * Return a random integer including both bounds.
 */
function randomInt(minimum, maximum) {
  return Math.floor(Math.random() * (maximum - minimum + 1)) + minimum;
}

/**
 * Return the next higher Fibonacci speed value.
 */
function nextFibonacciSpeed(speed) {
  if (speed < MIN_SPEED) {
    return MIN_SPEED;
  }

  let previousSpeed = 1;
  let currentSpeed = 2;
  while (currentSpeed <= speed) {
    const nextSpeed = previousSpeed + currentSpeed;
    previousSpeed = currentSpeed;
    currentSpeed = nextSpeed;
  }
  return currentSpeed;
}

/**
 * Return the next lower Fibonacci speed value.
 */
function previousFibonacciSpeed(speed) {
  if (speed <= MIN_SPEED) {
    return MIN_SPEED;
  }

  let previousSpeed = 1;
  let currentSpeed = 2;
  while (currentSpeed < speed) {
    const nextSpeed = previousSpeed + currentSpeed;
    previousSpeed = currentSpeed;
    currentSpeed = nextSpeed;
  }
  return previousSpeed;
}

/**
 * Parse a hex RGB color attribute and fall back to Pyliner orange.
 */
function parseColor(value) {
  if (!value) {
    return DEFAULT_COLOR;
  }

  const normalized = value.trim().replace("#", "");
  if (!/^[0-9a-fA-F]{6}$/.test(normalized)) {
    return DEFAULT_COLOR;
  }

  return [
    Number.parseInt(normalized.slice(0, 2), 16),
    Number.parseInt(normalized.slice(2, 4), 16),
    Number.parseInt(normalized.slice(4, 6), 16),
  ];
}

/**
 * Return the screen side opposite to the provided side.
 */
function oppositeSide(side) {
  return {
    top: "bottom",
    right: "left",
    bottom: "top",
    left: "right",
  }[side];
}

/**
 * Create one moving point on the requested canvas side.
 */
function randomPointOnSide(side, width, height, offsetMinimum, offsetMaximum) {
  const xPosition =
    side === "left" ? 0 : side === "right" ? width - 1 : Math.random() * (width - 1);
  const yPosition =
    side === "top" ? 0 : side === "bottom" ? height - 1 : Math.random() * (height - 1);

  return new EdgePoint(
    side,
    xPosition,
    yPosition,
    randomInt(15, 165),
    randomInt(offsetMinimum, offsetMaximum),
  );
}

/**
 * Create one animated line with two points on opposite sides.
 */
function randomLine(width, height, lineId, offsetMinimum, offsetMaximum) {
  const sides = ["top", "right", "bottom", "left"];
  const startSide = sides[randomInt(0, sides.length - 1)];

  return {
    id: lineId,
    start: randomPointOnSide(startSide, width, height, offsetMinimum, offsetMaximum),
    end: randomPointOnSide(
      oppositeSide(startSide),
      width,
      height,
      offsetMinimum,
      offsetMaximum,
    ),
    history: [],
  };
}

/**
 * Web Component that renders Pyliner in a bounded canvas.
 */
export class PylinerOverlay extends HTMLElement {
  /** Create the canvas, framebuffer state, and bound event handlers. */
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.canvas = document.createElement("canvas");
    this.help = document.createElement("div");
    this.context = this.canvas.getContext("2d", { alpha: true });
    this.imageData = null;
    this.pixelBuffer = null;
    this.brightness = null;
    this.canvas.hidden = true;
    this.help.hidden = true;
    this.lines = [];
    this.nextLineId = 0;
    this.animationFrame = 0;
    this.lastStepTime = 0;
    this.running = false;
    this.handleKeyDown = this.handleKeyDown.bind(this);
    this.handleResize = this.handleResize.bind(this);
    this.handleFullscreenChange = this.handleFullscreenChange.bind(this);
    this.stop = this.stop.bind(this);
    this.render = this.render.bind(this);
  }

  /**
   * Attach canvas, event handlers, and optional active startup.
   */
  connectedCallback() {
    this.shadowRoot.replaceChildren(this.buildStyle(), this.canvas, this.help);
    if (this.clickToStop) {
      this.canvas.addEventListener("click", this.stop);
    }
    window.addEventListener("keydown", this.handleKeyDown);
    window.addEventListener("resize", this.handleResize);
    document.addEventListener("fullscreenchange", this.handleFullscreenChange);
    this.applyLayoutAttributes();
    this.resize();

    if (this.hasAttribute("active")) {
      this.start();
    }
  }

  /**
   * Stop rendering and detach browser event handlers.
   */
  disconnectedCallback() {
    this.stop();
    this.canvas.removeEventListener("click", this.stop);
    window.removeEventListener("keydown", this.handleKeyDown);
    window.removeEventListener("resize", this.handleResize);
    document.removeEventListener("fullscreenchange", this.handleFullscreenChange);
  }

  /**
   * Observe layout attributes so embedding pages can resize the overlay.
   */
  static get observedAttributes() {
    return ["overlay-width", "overlay-height", "overlay-left", "overlay-top"];
  }

  /**
   * Apply changed overlay layout attributes while preserving runtime state.
   */
  attributeChangedCallback() {
    this.applyLayoutAttributes();
    if (this.running) {
      this.resize();
      this.clear();
    }
  }

  /**
   * Start a fresh overlay animation with the configured line count.
   */
  start() {
    if (this.running) {
      return;
    }

    this.running = true;
    this.setAttribute("active", "");
    this.canvas.hidden = false;
    this.help.hidden = true;
    this.resize();
    this.lines = [];
    this.nextLineId = 0;

    for (let index = 0; index < this.lineCount; index += 1) {
      this.lines.push(
        randomLine(
          this.width,
          this.height,
          this.nextLineId,
          this.offsetMinimum,
          this.offsetMaximum,
        ),
      );
      this.nextLineId += 1;
    }

    this.lastStepTime = performance.now();
    this.animationFrame = window.requestAnimationFrame(this.render);
  }

  /**
   * Stop animation, clear the canvas, and hide the overlay.
   */
  stop() {
    this.running = false;
    this.removeAttribute("active");
    this.removeAttribute("fullscreen");
    if (document.fullscreenElement === this) {
      document.exitFullscreen?.();
    }
    window.cancelAnimationFrame(this.animationFrame);
    this.clear();
    this.canvas.hidden = true;
    this.help.hidden = true;
  }

  /**
   * Toggle the overlay between running and stopped states.
   */
  toggle() {
    if (this.running) {
      this.stop();
      return;
    }

    this.start();
  }

  /**
   * Add one animated line when the runtime limit allows it.
   */
  addLine() {
    if (this.lines.length >= MAX_LINE_COUNT) {
      return;
    }

    this.lines.push(
      randomLine(
        this.width,
        this.height,
        this.nextLineId,
        this.offsetMinimum,
        this.offsetMaximum,
      ),
    );
    this.nextLineId += 1;
  }

  /**
   * Remove the oldest animated line and clear stale pixels immediately.
   */
  removeLine() {
    if (this.lines.length <= MIN_LINE_COUNT) {
      return;
    }

    this.lines.shift();
    this.clear();
  }

  /**
   * Increase animation speed to the next Fibonacci value.
   */
  speedUp() {
    this.speed = nextFibonacciSpeed(this.speed);
  }

  /**
   * Decrease animation speed to the previous Fibonacci value.
   */
  speedDown() {
    this.speed = previousFibonacciSpeed(this.speed);
  }

  /**
   * Increase the line thickness for newly rendered frames.
   */
  increaseThickness() {
    this.thickness = this.thickness + 1;
  }

  /**
   * Decrease the line thickness for newly rendered frames.
   */
  decreaseThickness() {
    this.thickness = this.thickness - 1;
  }

  /**
   * Toggle the runtime help overlay.
   */
  toggleHelp() {
    this.help.hidden = !this.help.hidden;
    if (!this.keyboardControls) {
      this.help.textContent = "Use the Pyliner view menu for controls.";
      return;
    }

    const helpLines = [
      "q/a: line count",
      "w/s: speed",
      "e/d: thickness",
      "h: help",
      "f: fullscreen",
      this.clickToStop ? "Esc/click: quit" : "Esc: quit",
    ];
    this.help.textContent = helpLines.join("\n");
  }

  /** Return the configured line count within runtime limits. */
  get lineCount() {
    return Math.max(
      MIN_LINE_COUNT,
      Math.min(MAX_LINE_COUNT, Number(this.getAttribute("lines")) || 1),
    );
  }

  /** Return the positive history length. */
  get history() {
    return Math.max(1, Number(this.getAttribute("history")) || 150);
  }

  /** Return the positive frame rate. */
  get speed() {
    return Math.max(MIN_SPEED, Number(this.getAttribute("speed")) || 10);
  }

  /** Store a positive frame rate in the component attributes. */
  set speed(value) {
    this.setAttribute("speed", String(Math.max(MIN_SPEED, value)));
  }

  /** Return the positive line thickness. */
  get thickness() {
    return Math.max(1, Number(this.getAttribute("thickness")) || 3);
  }

  /** Store a positive line thickness in the component attributes. */
  set thickness(value) {
    this.setAttribute("thickness", String(Math.max(1, value)));
  }

  /** Return whether keyboard controls are enabled. */
  get keyboardControls() {
    return this.getAttribute("keyboard-controls") !== "false";
  }

  /** Return whether a canvas click stops the animation. */
  get clickToStop() {
    return this.getAttribute("click-to-stop") !== "false";
  }

  /** Return the positive minimum endpoint movement. */
  get offsetMinimum() {
    return Math.max(1, Number(this.getAttribute("offset-min")) || 5);
  }

  /** Return the maximum endpoint movement, bounded by the minimum. */
  get offsetMaximum() {
    return Math.max(
      this.offsetMinimum,
      Number(this.getAttribute("offset-max")) || 20,
    );
  }

  /** Return whether old pixels fade to transparency. */
  get transparentBackground() {
    return this.hasAttribute("transparent-background");
  }

  /**
   * Build scoped styles for the bounded overlay rectangle.
   */
  buildStyle() {
    const style = document.createElement("style");
    style.textContent = `
      :host {
        position: fixed;
        inset: 0;
        z-index: 2147483647;
        pointer-events: none;
        --pyliner-overlay-width: 50vw;
        --pyliner-overlay-height: 50vh;
        --pyliner-overlay-left: 50vw;
        --pyliner-overlay-top: 50vh;
      }

      canvas {
        position: fixed;
        left: var(--pyliner-overlay-left);
        top: var(--pyliner-overlay-top);
        width: var(--pyliner-overlay-width);
        height: var(--pyliner-overlay-height);
        transform: translate(-50%, -50%);
        display: block;
        box-sizing: border-box;
        border: 2px solid rgb(255, 102, 0);
        background: black;
        pointer-events: auto;
      }

      :host([frameless]) canvas {
        border: 0;
      }

      :host([transparent-background]) canvas {
        background: transparent;
      }

      :host([fullscreen]) canvas {
        left: 50vw;
        top: 50vh;
        width: 100vw;
        height: 100vh;
        border: 0;
      }

      canvas[hidden],
      div[hidden] {
        display: none;
      }

      div {
        position: fixed;
        left: var(--pyliner-overlay-left);
        top: var(--pyliner-overlay-top);
        width: var(--pyliner-overlay-width);
        height: var(--pyliner-overlay-height);
        box-sizing: border-box;
        padding: 16px;
        transform: translate(-50%, -50%);
        color: white;
        font: 16px/1.6 system-ui, sans-serif;
        text-shadow: 0 1px 3px black;
        pointer-events: none;
        white-space: pre;
      }

      :host([fullscreen]) div {
        left: 50vw;
        top: 50vh;
        width: 100vw;
        height: 100vh;
      }
    `;
    return style;
  }

  /**
   * Map layout attributes to CSS custom properties.
   */
  applyLayoutAttributes() {
    this.style.setProperty(
      "--pyliner-overlay-width",
      this.getAttribute("overlay-width") || "50vw",
    );
    this.style.setProperty(
      "--pyliner-overlay-height",
      this.getAttribute("overlay-height") || "50vh",
    );
    this.style.setProperty(
      "--pyliner-overlay-left",
      this.getAttribute("overlay-left") || "50vw",
    );
    this.style.setProperty(
      "--pyliner-overlay-top",
      this.getAttribute("overlay-top") || "50vh",
    );
  }

  /**
   * Resize the backing canvas to match the displayed overlay rectangle.
   */
  resize() {
    const bounds = this.canvas.getBoundingClientRect();
    this.width = Math.max(2, Math.round(bounds.width));
    this.height = Math.max(2, Math.round(bounds.height));
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.resetFrameBuffer();
  }

  /**
   * Keep the canvas backing store aligned after viewport changes.
   */
  handleResize() {
    if (!this.running) {
      return;
    }

    this.resize();
    this.clear();
  }

  /**
   * Keep overlay sizing synchronized with browser fullscreen state.
   */
  handleFullscreenChange() {
    if (document.fullscreenElement === this) {
      this.setAttribute("fullscreen", "");
    } else {
      this.removeAttribute("fullscreen");
    }

    if (this.running) {
      this.resize();
      this.clear();
    }
  }

  /**
   * Clear the overlay canvas without changing line state.
   */
  clear() {
    this.resetFrameBuffer();
    this.context.putImageData(this.imageData, 0, 0);
  }

  /**
   * Create a pixel buffer matching the configured background mode.
   */
  resetFrameBuffer() {
    this.imageData = this.context.createImageData(this.width, this.height);
    this.pixelBuffer = this.imageData.data;
    this.brightness = new Uint8ClampedArray(this.width * this.height);

    if (!this.transparentBackground) {
      for (let index = 3; index < this.pixelBuffer.length; index += 4) {
        this.pixelBuffer[index] = 255;
      }
    }
  }

  /**
   * Drive animation frames while respecting the configured speed.
   */
  render(timestamp) {
    if (!this.running) {
      return;
    }

    const frameInterval = 1000 / this.speed;
    if (timestamp - this.lastStepTime >= frameInterval) {
      this.step();
      this.lastStepTime = timestamp;
    }

    this.animationFrame = window.requestAnimationFrame(this.render);
  }

  /**
   * Draw one logical animation step for all active lines.
   */
  step() {
    this.fadeFrameBuffer();
    const offsetMinimum = this.offsetMinimum;
    const offsetMaximum = this.offsetMaximum;

    for (const line of this.lines) {
      this.drawLine(line);
      line.start = line.start.moved(
        this.width,
        this.height,
        offsetMinimum,
        offsetMaximum,
      );
      line.end = line.end.moved(
        this.width,
        this.height,
        offsetMinimum,
        offsetMaximum,
      );
      line.history.push(1);

      if (line.history.length > this.history) {
        line.history.shift();
      }
    }

    this.context.putImageData(this.imageData, 0, 0);
  }

  /**
   * Fade framebuffer pixels toward black or transparency.
   */
  fadeFrameBuffer() {
    const fadeStep = Math.max(1, Math.round(255 / this.history));
    const transparentBackground = this.transparentBackground;

    for (let index = 0; index < this.pixelBuffer.length; index += 4) {
      if (transparentBackground) {
        this.pixelBuffer[index + 3] = Math.max(
          0,
          this.pixelBuffer[index + 3] - fadeStep,
        );
      } else {
        this.pixelBuffer[index] = Math.max(0, this.pixelBuffer[index] - fadeStep);
        this.pixelBuffer[index + 1] = Math.max(
          0,
          this.pixelBuffer[index + 1] - fadeStep,
        );
        this.pixelBuffer[index + 2] = Math.max(
          0,
          this.pixelBuffer[index + 2] - fadeStep,
        );
      }
    }

    for (let index = 0; index < this.brightness.length; index += 1) {
      this.brightness[index] = Math.max(0, this.brightness[index] - fadeStep);
    }
  }

  /**
   * Draw one line into the explicit framebuffer.
   */
  drawLine(line) {
    const [startX, startY] = line.start.toXY(this.width, this.height);
    const [endX, endY] = line.end.toXY(this.width, this.height);
    const pixels = this.linePixelIndexes(startX, startY, endX, endY);
    const [red, green, blue] = parseColor(this.getAttribute("color"));
    const transparentBackground = this.transparentBackground;

    for (const pixelIndex of pixels) {
      const bufferIndex = pixelIndex * 4;
      const isCovered = transparentBackground
        ? this.pixelBuffer[bufferIndex + 3] > 0
        : this.pixelBuffer[bufferIndex] > 0 ||
          this.pixelBuffer[bufferIndex + 1] > 0 ||
          this.pixelBuffer[bufferIndex + 2] > 0;

      if (isCovered) {
        this.brightness[pixelIndex] = Math.min(255, this.brightness[pixelIndex] + 24);
      }

      const brightness = this.brightness[pixelIndex] / 255;
      this.pixelBuffer[bufferIndex] = Math.round(red + (255 - red) * brightness);
      this.pixelBuffer[bufferIndex + 1] = Math.round(green + (255 - green) * brightness);
      this.pixelBuffer[bufferIndex + 2] = Math.round(blue + (255 - blue) * brightness);
      this.pixelBuffer[bufferIndex + 3] = 255;
    }
  }

  /**
   * Rasterize a thick line to unique framebuffer pixel indexes.
   */
  linePixelIndexes(startX, startY, endX, endY) {
    const indexes = new Set();
    const width = this.width;
    const height = this.height;
    const pixelCount = Math.max(Math.abs(endX - startX), Math.abs(endY - startY)) + 1;
    const thickness = this.thickness;
    const beforeCenter = Math.floor(thickness / 2);
    const afterCenter = thickness - beforeCenter;

    for (let step = 0; step < pixelCount; step += 1) {
      const ratio = pixelCount === 1 ? 0 : step / (pixelCount - 1);
      const xPosition = Math.round(startX + (endX - startX) * ratio);
      const yPosition = Math.round(startY + (endY - startY) * ratio);

      for (let xOffset = -beforeCenter; xOffset < afterCenter; xOffset += 1) {
        for (let yOffset = -beforeCenter; yOffset < afterCenter; yOffset += 1) {
          const xPixel = xPosition + xOffset;
          const yPixel = yPosition + yOffset;

          if (xPixel >= 0 && xPixel < width && yPixel >= 0 && yPixel < height) {
            indexes.add(yPixel * width + xPixel);
          }
        }
      }
    }

    return indexes;
  }

  /**
   * Toggle browser fullscreen and component fullscreen layout together.
   */
  toggleFullscreen() {
    if (document.fullscreenElement) {
      document.exitFullscreen?.();
      return;
    }

    this.requestFullscreen?.();
  }

  /**
   * Handle Easter egg startup and runtime overlay controls.
   */
  handleKeyDown(event) {
    if (!this.keyboardControls) {
      return;
    }

    if (!this.running && event.ctrlKey && event.altKey && event.key.toLowerCase() === "p") {
      event.preventDefault();
      this.start();
      return;
    }

    if (!this.running) {
      return;
    }

    if (event.key === "Escape") {
      this.stop();
    } else if (event.key === "q" && this.lines.length < MAX_LINE_COUNT) {
      this.addLine();
    } else if (event.key === "a" && this.lines.length > MIN_LINE_COUNT) {
      this.removeLine();
    } else if (event.key === "w") {
      this.speedUp();
    } else if (event.key === "s") {
      this.speedDown();
    } else if (event.key === "e") {
      this.increaseThickness();
    } else if (event.key === "d") {
      this.decreaseThickness();
    } else if (event.key === "h") {
      this.toggleHelp();
    } else if (event.key === "f") {
      this.toggleFullscreen();
    }
  }
}

customElements.define("pyliner-overlay", PylinerOverlay);
