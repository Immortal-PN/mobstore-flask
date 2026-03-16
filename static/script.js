const reveals = document.querySelectorAll(".reveal");

const revealOnScroll = () => {
    const visibleEdge = window.innerHeight - 80;
    reveals.forEach((element) => {
        if (element.getBoundingClientRect().top < visibleEdge) {
            element.classList.add("active");
        }
    });
};

window.addEventListener("scroll", revealOnScroll);
window.addEventListener("load", revealOnScroll);

document.querySelectorAll("[data-copy-target]").forEach((button) => {
    button.addEventListener("click", async () => {
        const target = document.getElementById(button.dataset.copyTarget);
        if (!target) {
            return;
        }

        await navigator.clipboard.writeText(target.value);
        button.textContent = "Copied";
        window.setTimeout(() => {
            button.textContent = "Copy";
        }, 1600);
    });
});
