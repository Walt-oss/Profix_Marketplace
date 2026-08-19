/* Pro Fix — shared frontend helpers. Linked from every template. */

function initials(name){
  return name.split(' ').filter(Boolean).map(n => n[0]).join('').toUpperCase();
}

let __toastTimer;
function showToast(msg){
  const toast = document.getElementById('toast');
  if(!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(__toastTimer);
  __toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}

/* Marks the current page's tab active and wires up any tab that
   doesn't have a real route yet (data-placeholder) to show a toast
   instead of linking somewhere that doesn't exist. */
function wireTabBar(current){
  document.querySelectorAll('.tab').forEach(tab => {
    if(tab.dataset.tab === current) tab.classList.add('active');
  });
  document.querySelectorAll('.tab[data-placeholder]').forEach(tab => {
    tab.addEventListener('click', () => {
      const label = tab.querySelector('span')?.textContent || 'This section';
      showToast(label + ' — coming soon');
    });
  });
}
