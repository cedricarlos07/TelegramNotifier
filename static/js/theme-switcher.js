/**
 * Theme Switcher for KODJO ENGLISH BOT
 * Allows switching between light and dark themes
 * with smooth transitions and persistent settings via localStorage
 */

document.addEventListener('DOMContentLoaded', function() {
    // Theme switching elements
    const themeSwitcher = document.getElementById('theme-switcher');
    const themeSwitcherMenu = document.getElementById('theme-switcher-menu');
    const themeSwitcherMobile = document.getElementById('theme-switcher-mobile');
    const html = document.documentElement;
    
    // Theme mode indicators
    const darkIcons = document.querySelectorAll('.theme-icon-dark');
    const lightIcons = document.querySelectorAll('.theme-icon-light');
    const darkTexts = document.querySelectorAll('.theme-text-dark');
    const lightTexts = document.querySelectorAll('.theme-text-light');
    
    // Check if the user has a preferred theme saved in localStorage
    const savedTheme = localStorage.getItem('kodjo-theme');
    
    // Apply the saved theme or default to dark theme
    if (savedTheme) {
        applyTheme(savedTheme);
    } else {
        // Check if user has system preference for light mode
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            applyTheme('light');
        } else {
            applyTheme('dark');
        }
    }
    
    // Theme switching functions
    function applyTheme(theme) {
        if (theme === 'light') {
            html.setAttribute('data-bs-theme', 'light');
            toggleThemeVisuals('light');
            localStorage.setItem('kodjo-theme', 'light');
        } else {
            html.setAttribute('data-bs-theme', 'dark');
            toggleThemeVisuals('dark');
            localStorage.setItem('kodjo-theme', 'dark');
        }
    }
    
    function toggleThemeVisuals(theme) {
        if (theme === 'light') {
            // Show sun icons, hide moon icons
            darkIcons.forEach(icon => icon.classList.add('d-none'));
            lightIcons.forEach(icon => icon.classList.remove('d-none'));
            
            // Show dark mode text, hide light mode text
            darkTexts.forEach(text => text.classList.add('d-none'));
            lightTexts.forEach(text => text.classList.remove('d-none'));
        } else {
            // Show moon icons, hide sun icons
            darkIcons.forEach(icon => icon.classList.remove('d-none'));
            lightIcons.forEach(icon => icon.classList.add('d-none'));
            
            // Show light mode text, hide dark mode text
            darkTexts.forEach(text => text.classList.remove('d-none'));
            lightTexts.forEach(text => text.classList.add('d-none'));
        }
    }
    
    function toggleTheme() {
        const currentTheme = html.getAttribute('data-bs-theme');
        if (currentTheme === 'dark') {
            applyTheme('light');
        } else {
            applyTheme('dark');
        }
    }
    
    // Add event listeners to theme toggles
    if (themeSwitcher) {
        themeSwitcher.addEventListener('click', toggleTheme);
    }
    
    if (themeSwitcherMenu) {
        themeSwitcherMenu.addEventListener('click', toggleTheme);
    }
    
    if (themeSwitcherMobile) {
        themeSwitcherMobile.addEventListener('click', toggleTheme);
    }
    
    // Listen for system theme changes
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (!localStorage.getItem('kodjo-theme')) {
                applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
});