/**
 * Theme Switcher for CourseHub
 * Allows switching between light and dark themes
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get HTML element
    const htmlElement = document.documentElement;
    
    // Theme switcher elements
    const themeSwitchers = [
        document.getElementById('theme-switcher'),
        document.getElementById('theme-switcher-menu'),
        document.getElementById('theme-switcher-mobile')
    ].filter(Boolean); // Filter out null elements if they don't exist
    
    // Theme icons and text
    const darkIcons = document.querySelectorAll('.theme-icon-dark');
    const lightIcons = document.querySelectorAll('.theme-icon-light');
    const darkTexts = document.querySelectorAll('.theme-text-dark');
    const lightTexts = document.querySelectorAll('.theme-text-light');
    
    // Function to get current theme from localStorage or default to dark
    const getCurrentTheme = () => {
        return localStorage.getItem('theme') || 'dark';
    };
    
    // Function to set theme
    const setTheme = (theme) => {
        // Set data-bs-theme attribute
        htmlElement.setAttribute('data-bs-theme', theme);
        
        // Store theme preference in localStorage
        localStorage.setItem('theme', theme);
        
        // Update UI elements
        if (theme === 'light') {
            darkIcons.forEach(icon => icon.classList.add('d-none'));
            lightIcons.forEach(icon => icon.classList.remove('d-none'));
            darkTexts.forEach(text => text.classList.add('d-none'));
            lightTexts.forEach(text => text.classList.remove('d-none'));
        } else {
            darkIcons.forEach(icon => icon.classList.remove('d-none'));
            lightIcons.forEach(icon => icon.classList.add('d-none'));
            darkTexts.forEach(text => text.classList.remove('d-none'));
            lightTexts.forEach(text => text.classList.add('d-none'));
        }
    };
    
    // Toggle theme function
    const toggleTheme = () => {
        const currentTheme = getCurrentTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    };
    
    // Add click event to all theme switcher buttons
    themeSwitchers.forEach(switcher => {
        if (switcher) {
            switcher.addEventListener('click', toggleTheme);
        }
    });
    
    // Set initial theme on page load
    setTheme(getCurrentTheme());
});