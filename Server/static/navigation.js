const btn = document.getElementById('menu-btn');
const menu = document.getElementById('mobile-menu');
const bar1 = document.getElementById('bar-1');
const bar2 = document.getElementById('bar-2');
const bar3 = document.getElementById('bar-3');
let open = false;

btn.addEventListener('click', () => {
    open = !open;
    menu.classList.toggle('hidden', !open);
    bar1.style.transform = open ? 'translateY(6px) rotate(45deg)' : '';
    bar2.style.opacity = open ? '0' : '1';
    bar3.style.transform = open ? 'translateY(-6px) rotate(-45deg)' : '';
});