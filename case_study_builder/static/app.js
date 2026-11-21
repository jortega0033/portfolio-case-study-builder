"use strict";
(function () {
  var API = "/api/v1/projects";
  var CONFLICT_MSG = "This case study changed in another tab or session. Reload to see the latest version.";

  var $ = function (id) { return document.getElementById(id); };
  var els = {
    list: $("project-list"), newBtn: $("new-project"), form: $("editor"),
    empty: $("editor-empty"), body: $("editor-body"), title: $("title"),
    sections: $("sections"), sectionsEmpty: $("sections-empty"),
    add: $("add-section"), save: $("save"), status: $("status"),
    error: $("error"), reload: $("reload"), preview: $("preview-article")
  };

  var state = {
    project: null,   // {id, title, revision, sections:[{key,id,heading,body}]}
    dirty: false,
    saving: false,
    conflict: false,
    editSeq: 0,
    loadToken: 0,
    summaries: []
  };
  var keyCounter = 0;

  function nextKey() { keyCounter += 1; return "k" + keyCounter; }

  function api(method, url, body) {
    var opts = { method: method, headers: { "Accept": "application/json" }, cache: "no-store" };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    return fetch(url, opts).then(function (res) {
      return res.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { data = null; }
        if (!res.ok) {
          var err = (data && data.error) || {};
          var e2 = new Error(err.message || ("Request failed (" + res.status + ")"));
          e2.status = res.status;
          e2.code = err.code || "";
          e2.details = err.details || {};
          throw e2;
        }
        return data;
      });
    });
  }

  function describeError(err) {
    if (err && err.status) { return "Could not complete the request: " + err.message; }
    return "Could not reach the server. Your edits are still here; try again.";
  }

  function setStatus(msg) { els.status.textContent = msg; }
  function setError(msg) { els.error.textContent = msg || ""; }

  function toLocal(p) {
    return {
      id: p.id, title: p.title, revision: p.revision,
      sections: p.sections.map(function (s) {
        return { key: nextKey(), id: s.id, heading: s.heading, body: s.body };
      })
    };
  }

  function markDirty() {
    state.dirty = true;
    state.editSeq += 1;
    if (!state.saving) { setStatus("Unsaved changes"); }
    updateControls();
  }

  function updateControls() {
    var open = !!state.project;
    els.save.disabled = !open || state.saving || state.conflict;
    els.reload.hidden = !state.conflict;
  }

  /* ---------- preview ---------- */
  function renderPreview() {
    var art = els.preview;
    art.textContent = "";
    var p = state.project;
    if (!p) { return; }
    var titleHeading = document.createElement("h2");
    titleHeading.textContent = p.title;
    art.appendChild(titleHeading);
    p.sections.forEach(function (s) {
      if (s.heading.trim() !== "") {
        var sectionHeading = document.createElement("h3");
        sectionHeading.textContent = s.heading;
        art.appendChild(sectionHeading);
      }
      s.body.split(/\n\n+/).forEach(function (chunk) {
        if (chunk.trim() === "") { return; }
        var para = document.createElement("p");
        para.textContent = chunk;
        art.appendChild(para);
      });
    });
  }

  /* ---------- project list ---------- */
  function renderList() {
    els.list.textContent = "";
    state.summaries.forEach(function (s) {
      var li = document.createElement("li");
      var b = document.createElement("button");
      b.type = "button";
      b.dataset.id = s.id;
      var n = s.section_count;
      b.textContent = s.title + " (" + n + (n === 1 ? " section)" : " sections)");
      if (state.project && state.project.id === s.id) { b.setAttribute("aria-current", "true"); }
      li.appendChild(b);
      els.list.appendChild(li);
    });
  }

  function refreshList() {
    return api("GET", API).then(function (d) {
      state.summaries = d.projects || [];
      renderList();
    }).catch(function () { /* list refresh is best effort */ });
  }

  /* ---------- editor ---------- */
  function mkButton(text, label, cls, disabled, action, index) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = text;
    b.setAttribute("aria-label", label);
    b.dataset.action = action;
    b.dataset.index = String(index);
    if (disabled) { b.disabled = true; }
    return b;
  }

  function renderSections() {
    var host = els.sections;
    host.textContent = "";
    var secs = state.project ? state.project.sections : [];
    secs.forEach(function (s, i) {
      var n = i + 1;
      var fs = document.createElement("fieldset");
      fs.className = "section";
      fs.dataset.index = String(i);
      var lg = document.createElement("legend");
      lg.textContent = "Section " + n;
      fs.appendChild(lg);

      var f1 = document.createElement("div");
      f1.className = "field";
      var l1 = document.createElement("label");
      l1.htmlFor = "section-" + s.key + "-heading";
      l1.textContent = "Section " + n + " heading";
      var h = document.createElement("input");
      h.type = "text";
      h.id = l1.htmlFor;
      h.maxLength = 160;
      h.autocomplete = "off";
      h.placeholder = "Short heading for this part";
      h.value = s.heading;
      h.dataset.index = String(i);
      h.dataset.field = "heading";
      f1.appendChild(l1);
      f1.appendChild(h);

      var f2 = document.createElement("div");
      f2.className = "field";
      var l2 = document.createElement("label");
      l2.htmlFor = "section-" + s.key + "-body";
      l2.textContent = "Section " + n + " body";
      var t = document.createElement("textarea");
      t.id = l2.htmlFor;
      t.maxLength = 20000;
      t.placeholder = "Describe the problem the project solved";
      t.value = s.body;
      t.dataset.index = String(i);
      t.dataset.field = "body";
      f2.appendChild(l2);
      f2.appendChild(t);

      var tools = document.createElement("div");
      tools.className = "section-tools";
      tools.appendChild(mkButton("Move up", "Move section " + n + " up", "", i === 0, "up", i));
      tools.appendChild(mkButton("Move down", "Move section " + n + " down", "", i === secs.length - 1, "down", i));
      tools.appendChild(mkButton("Delete", "Delete section " + n, "", false, "delete", i));

      fs.appendChild(f1);
      fs.appendChild(f2);
      fs.appendChild(tools);
      host.appendChild(fs);
    });
    els.sectionsEmpty.hidden = secs.length !== 0;
  }

  function renderAll() {
    var open = !!state.project;
    els.empty.hidden = open;
    els.body.hidden = !open;
    if (open) {
      els.title.value = state.project.title;
      renderSections();
    } else {
      els.sections.textContent = "";
    }
    renderPreview();
    renderList();
    updateControls();
  }

  function focusSelector(sel) {
    var el = els.sections.querySelector(sel);
    if (el && !el.disabled) { el.focus(); return true; }
    return false;
  }

  function moveSection(i, dir, fromField) {
    var secs = state.project.sections;
    var j = i + dir;
    if (j < 0 || j >= secs.length) { return; }
    var tmp = secs[i]; secs[i] = secs[j]; secs[j] = tmp;
    markDirty();
    renderSections();
    renderPreview();
    if (fromField) {
      focusSelector('[data-index="' + j + '"][data-field="' + fromField + '"]');
    } else {
      var same = dir < 0 ? "up" : "down";
      var other = dir < 0 ? "down" : "up";
      if (!focusSelector('button[data-action="' + same + '"][data-index="' + j + '"]')) {
        focusSelector('button[data-action="' + other + '"][data-index="' + j + '"]');
      }
    }
    setStatus("Section moved to position " + (j + 1) + " (unsaved)");
  }

  function deleteSection(i) {
    var secs = state.project.sections;
    secs.splice(i, 1);
    markDirty();
    renderSections();
    renderPreview();
    var target = secs.length === 0 ? -1 : Math.min(i, secs.length - 1);
    if (target < 0 || !focusSelector('input[data-index="' + target + '"][data-field="heading"]')) {
      els.add.focus();
    }
    setStatus("Section deleted (unsaved)");
  }

  function addSection() {
    if (!state.project) { return; }
    state.project.sections.push({ key: nextKey(), id: null, heading: "", body: "" });
    markDirty();
    renderSections();
    renderPreview();
    var idx = state.project.sections.length - 1;
    focusSelector('input[data-index="' + idx + '"][data-field="heading"]');
    setStatus("Section " + (idx + 1) + " added (unsaved)");
  }

  /* ---------- load / open ---------- */
  function showProject(p) {
    state.project = toLocal(p);
    state.dirty = false;
    state.conflict = false;
    state.editSeq = 0;
    setError("");
    renderAll();
  }

  function setHash(id) {
    var want = id ? "#" + id : "";
    if (location.hash !== want) {
      history.replaceState(null, "", location.pathname + location.search + want);
    }
  }

  function openProject(id) {
    var token = ++state.loadToken;
    setStatus("Loading…");
    return api("GET", API + "/" + encodeURIComponent(id)).then(function (p) {
      if (token !== state.loadToken) { return; }
      showProject(p);
      setHash(p.id);
      setStatus("Loaded revision " + p.revision);
      els.title.focus();
    }).catch(function (err) {
      if (token !== state.loadToken) { return; }
      setStatus("");
      setError(err.status === 404 ? "That case study was not found." : describeError(err));
      throw err;
    });
  }

  function confirmLeave() {
    if (!state.dirty) { return true; }
    return window.confirm("You have unsaved changes. Discard them?");
  }

  function createProject() {
    if (!confirmLeave()) { return; }
    setError("");
    setStatus("Creating…");
    els.newBtn.disabled = true;
    api("POST", API, {}).then(function (p) {
      state.loadToken += 1;
      showProject(p);
      setHash(p.id);
      setStatus("Created case study (revision " + p.revision + ")");
      els.title.focus();
      return refreshList();
    }).catch(function (err) {
      setStatus("");
      setError(describeError(err));
    }).then(function () { els.newBtn.disabled = false; });
  }

  /* ---------- save ---------- */
  function save() {
    if (!state.project || state.saving || state.conflict) { return; }
    var p = state.project;
    var sentKeys = p.sections.map(function (s) { return s.key; });
    var seqAtSend = state.editSeq;
    var payload = {
      title: p.title,
      base_revision: p.revision,
      sections: p.sections.map(function (s) {
        var o = { heading: s.heading, body: s.body };
        if (s.id) { o.id = s.id; }
        return o;
      })
    };
    state.saving = true;
    setError("");
    setStatus("Saving…");
    updateControls();
    api("PUT", API + "/" + encodeURIComponent(p.id), payload).then(function (res) {
      state.saving = false;
      if (state.project !== p) { updateControls(); return; }
      p.revision = res.revision;
      var edited = state.editSeq !== seqAtSend;
      res.sections.forEach(function (rs, i) {
        var local = p.sections.filter(function (s) { return s.key === sentKeys[i]; })[0];
        if (!local) { return; }
        local.id = rs.id;
        if (!edited) { local.heading = rs.heading; local.body = rs.body; }
      });
      if (!edited) {
        p.title = res.title;
        state.dirty = false;
        syncFields();
        renderPreview();
        setStatus("Saved (revision " + res.revision + ")");
      } else {
        setStatus("Saved (revision " + res.revision + "), newer edits are unsaved");
      }
      updateControls();
      refreshList();
    }).catch(function (err) {
      state.saving = false;
      if (state.project !== p) { updateControls(); return; }
      if (err && err.status === 409) {
        state.conflict = true;
        setStatus("Unsaved changes");
        setError(CONFLICT_MSG);
      } else {
        setStatus("Unsaved changes");
        setError(describeError(err));
      }
      updateControls();
      if (state.conflict) { els.reload.focus(); }
    });
  }

  function syncFields() {
    var p = state.project;
    if (els.title.value !== p.title) { els.title.value = p.title; }
    p.sections.forEach(function (s, i) {
      var h = els.sections.querySelector('[data-index="' + i + '"][data-field="heading"]');
      var b = els.sections.querySelector('[data-index="' + i + '"][data-field="body"]');
      if (h && h.value !== s.heading) { h.value = s.heading; }
      if (b && b.value !== s.body) { b.value = s.body; }
    });
  }

  function reloadLatest() {
    if (!state.project) { return; }
    var id = state.project.id;
    setError("");
    openProject(id).then(function () { return refreshList(); }).catch(function () {});
  }

  /* ---------- events ---------- */
  els.title.addEventListener("input", function () {
    if (!state.project) { return; }
    state.project.title = els.title.value;
    markDirty();
    renderPreview();
  });

  els.sections.addEventListener("input", function (e) {
    var t = e.target;
    if (!t.dataset || !t.dataset.field || !state.project) { return; }
    var s = state.project.sections[Number(t.dataset.index)];
    if (!s) { return; }
    s[t.dataset.field] = t.value;
    markDirty();
    renderPreview();
  });

  els.sections.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest("button[data-action]") : null;
    if (!b || b.disabled) { return; }
    var i = Number(b.dataset.index);
    if (b.dataset.action === "up") { moveSection(i, -1, null); }
    else if (b.dataset.action === "down") { moveSection(i, 1, null); }
    else if (b.dataset.action === "delete") { deleteSection(i); }
  });

  els.sections.addEventListener("keydown", function (e) {
    var t = e.target;
    if (!e.altKey || e.ctrlKey || e.metaKey || !t.dataset || !t.dataset.field) { return; }
    if (e.key === "ArrowUp" || e.key === "ArrowDown") {
      e.preventDefault();
      moveSection(Number(t.dataset.index), e.key === "ArrowUp" ? -1 : 1, t.dataset.field);
    }
  });

  els.add.addEventListener("click", addSection);
  els.newBtn.addEventListener("click", createProject);
  els.reload.addEventListener("click", reloadLatest);
  els.form.addEventListener("submit", function (e) { e.preventDefault(); save(); });

  els.list.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest("button[data-id]") : null;
    if (!b) { return; }
    if (state.project && state.project.id === b.dataset.id && !state.conflict) { return; }
    if (!confirmLeave()) { return; }
    openProject(b.dataset.id).catch(function () {});
  });

  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && !e.altKey && (e.key === "s" || e.key === "S")) {
      e.preventDefault();
      save();
    }
  });

  window.addEventListener("beforeunload", function (e) {
    if (state.dirty) {
      e.preventDefault();
      e.returnValue = "";
    }
  });

  window.addEventListener("hashchange", function () {
    var id = location.hash.replace(/^#/, "");
    if (!id || (state.project && state.project.id === id)) { return; }
    if (!confirmLeave()) { setHash(state.project ? state.project.id : ""); return; }
    openProject(id).catch(function () {});
  });

  /* ---------- init ---------- */
  function init() {
    renderAll();
    api("GET", API).then(function (d) {
      state.summaries = d.projects || [];
      renderList();
      var want = location.hash.replace(/^#/, "");
      var ids = state.summaries.map(function (s) { return s.id; });
      var pick = ids.indexOf(want) >= 0 ? want : (ids.length ? ids[0] : "");
      if (!pick) {
        setStatus("No case studies yet. Select \"New case study\" to begin.");
        return;
      }
      return openProject(pick);
    }).catch(function (err) {
      setError(describeError(err));
    });
  }
  init();
})();
