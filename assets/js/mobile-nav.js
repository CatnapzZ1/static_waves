// Enhance the existing PaperMod menu; no duplicate links or theme override.
(() => {
  const menu = document.getElementById('menu');
  const nav = menu?.parentElement;
  if (!nav || !menu.children.length || typeof HTMLDialogElement === 'undefined' ||
      typeof HTMLDialogElement.prototype.showModal !== 'function') return;

  const mobile = window.matchMedia('(max-width: 768px)');
  const position = document.createComment('Original PaperMod menu position');
  menu.before(position);

  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'mobile-menu-toggle';
  toggle.setAttribute('aria-label', '打开导航菜单');
  toggle.setAttribute('aria-controls', 'mobile-nav-drawer');
  toggle.setAttribute('aria-expanded', 'false');
  toggle.setAttribute('aria-haspopup', 'dialog');
  toggle.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>';
  nav.append(toggle);

  const drawer = document.createElement('dialog');
  drawer.id = 'mobile-nav-drawer';
  drawer.className = 'mobile-nav-drawer';
  drawer.setAttribute('aria-labelledby', 'mobile-nav-title');
  drawer.innerHTML = '<div class="mobile-nav-heading"><h2 id="mobile-nav-title">导航</h2><button type="button" class="mobile-nav-close" aria-label="关闭导航菜单" autofocus><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg></button></div><nav aria-label="移动端主导航"></nav>';
  document.body.append(drawer);
  const drawerNav = drawer.querySelector('nav');
  const close = () => {
    if (drawer.open) drawer.close();
    toggle.setAttribute('aria-expanded', 'false');
    document.documentElement.classList.remove('nav-drawer-open');
  };

  toggle.addEventListener('click', () => {
    if (!mobile.matches || drawer.open) return;
    drawer.showModal();
    toggle.setAttribute('aria-expanded', 'true');
    document.documentElement.classList.add('nav-drawer-open');
  });
  drawer.querySelector('button').addEventListener('click', close);
  drawer.addEventListener('cancel', event => {
    event.preventDefault();
    close();
  });
  drawer.addEventListener('close', () => {
    // A queued close event must not close a drawer that has already reopened.
    if (!drawer.open) close();
  });
  // Require both press and release on the backdrop, not a drag out of the panel.
  let backdropPress = false;
  const outside = event => {
    const rect = drawer.getBoundingClientRect();
    return event.clientX < rect.left || event.clientX > rect.right ||
      event.clientY < rect.top || event.clientY > rect.bottom;
  };
  drawer.addEventListener('pointerdown', event => {
    backdropPress = event.target === drawer && outside(event);
  });
  drawer.addEventListener('click', event => {
    if (backdropPress && event.target === drawer && outside(event)) close();
    backdropPress = false;
    if (event.target.closest('a[href]')) close();
  });

  const syncLayout = () => {
    close();
    if (mobile.matches) {
      drawerNav.append(menu);
    } else {
      position.after(menu);
    }
    toggle.hidden = !mobile.matches;
  };
  mobile.addEventListener('change', syncLayout);
  // A page restored from the browser back/forward cache must not stay locked.
  window.addEventListener('pageshow', syncLayout);
  syncLayout();
  document.documentElement.classList.add('nav-drawer-ready');
})();
