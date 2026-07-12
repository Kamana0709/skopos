/**
 * components/chip-input.js
 * An accessible multi-value tag input. Enter/comma commits a chip,
 * Backspace on an empty field removes the last chip.
 */
import { el, clear } from "../dom-utils.js";

export function createChipInput(mountPoint, options) {
    const { initialValues = [], max, placeholder, fieldLabel, onChange, validateLabel } = options;
    let values = [...initialValues];

    const wrapper = el("div", { class: "chip-input" });
    const liveRegion = el("span", { class: "u-sr-only", "aria-live": "polite" });
    const input = el("input", {
        type: "text",
        class: "chip-input__field",
        placeholder: values.length >= max ? "" : placeholder,
        "aria-label": fieldLabel,
    });

    function renderChips() {
        wrapper.querySelectorAll(".chip-input__chip").forEach((c) => c.remove());
        values.forEach((value, index) => {
            const chip = el("span", { class: "chip-input__chip" }, [
                value,
                el(
                    "button",
                    {
                        type: "button",
                        class: "chip-input__chip-remove",
                        "aria-label": `Remove ${value}`,
                        onClick: () => removeAt(index),
                    },
                    ["×"]
                ),
            ]);
            wrapper.insertBefore(chip, input);
        });
        const atMax = values.length >= max;
        wrapper.classList.toggle("chip-input--at-max", atMax);
        input.disabled = atMax;
        input.placeholder = atMax ? `Max ${max} reached` : placeholder;
    }

    function commit(rawLabel) {
        const label = rawLabel.trim();
        if (!label) return;
        if (values.length >= max) return;
        if (values.some((v) => v.toLowerCase() === label.toLowerCase())) {
            input.value = "";
            return;
        }
        if (validateLabel) {
            const error = validateLabel(label);
            if (error) return;
        }
        values.push(label);
        input.value = "";
        renderChips();
        onChange([...values]);
        liveRegion.textContent = `Added ${label}. ${values.length} of ${max}.`;
    }

    function removeAt(index) {
        const [removed] = values.splice(index, 1);
        renderChips();
        onChange([...values]);
        if (removed) liveRegion.textContent = `Removed ${removed}. ${values.length} of ${max}.`;
        input.focus();
    }

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            commit(input.value);
        } else if (e.key === "Backspace" && input.value === "" && values.length > 0) {
            removeAt(values.length - 1);
        }
    });

    input.addEventListener("blur", () => {
        if (input.value.trim()) commit(input.value);
    });

    wrapper.appendChild(input);
    clear(mountPoint);
    mountPoint.appendChild(wrapper);
    mountPoint.appendChild(liveRegion);
    renderChips();

    return {
        getValues: () => [...values],
        setValues: (next) => {
            values = [...next];
            renderChips();
        },
        focus: () => input.focus(),
    };
}