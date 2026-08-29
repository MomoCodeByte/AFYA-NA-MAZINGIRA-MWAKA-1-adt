(function () {
  "use strict";

  var BOOK_ID = "AFYA-NA-MAZINGIRA-MWAKA-1-adt";
  var pageMeta = document.querySelector('meta[name="page-section-id"]');
  var titleMeta = document.querySelector('meta[name="title-id"]');
  var pageNumber = pageMeta ? String(Number(pageMeta.content)) : "";
  var sectionId = titleMeta ? titleMeta.content : "page-" + pageNumber;
  if (!pageNumber) return;

  function element(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function storageKey(id) {
    return BOOK_ID + ":" + sectionId + ":" + id;
  }

  function stored(id) {
    try { return window.localStorage.getItem(storageKey(id)) || ""; }
    catch (_) { return ""; }
  }

  function remember(id, value) {
    try { window.localStorage.setItem(storageKey(id), value); }
    catch (_) { /* The answer control remains usable without storage. */ }
  }

  function bindValue(control, id) {
    control.name = id;
    control.value = stored(id);
    control.autocomplete = "off";
    control.addEventListener("input", function () { remember(id, control.value); });
    control.addEventListener("change", function () { remember(id, control.value); });
  }

  function normalize(value) {
    return String(value || "")
      .toLocaleLowerCase("sw-TZ")
      .replace(/[_\.]{2,}/g, " ")
      .replace(/[^a-z0-9à-ž]+/gi, " ")
      .trim()
      .replace(/\s+/g, " ");
  }

  function tokens(value) {
    return normalize(value).split(" ").filter(function (token) {
      return token.length > 1 || /^\d+$/.test(token);
    });
  }

  function lineGroups(page) {
    return Array.prototype.slice.call(page.querySelectorAll(".semantic-text-group")).filter(function (group) {
      return group.querySelector(".semantic-positioned-word");
    });
  }

  function scoreText(candidate, wanted) {
    var candidateText = normalize(candidate);
    var wantedText = normalize(wanted);
    if (!candidateText || !wantedText) return 0;
    if (!/^\d+$/.test(wantedText)) {
      candidateText = candidateText.replace(/^\d+\s+/, "");
      wantedText = wantedText.replace(/^\d+\s+/, "");
    }
    if (candidateText === wantedText) return 8;
    if (candidateText.indexOf(wantedText) !== -1 || wantedText.indexOf(candidateText) !== -1) return 5;
    var wantedTokens = tokens(wantedText);
    var candidateTokens = tokens(candidateText);
    if (!wantedTokens.length || !candidateTokens.length) return 0;
    var common = wantedTokens.filter(function (token) {
      return candidateTokens.indexOf(token) !== -1;
    }).length;
    var score = common / wantedTokens.length;
    if (wantedTokens[0] === candidateTokens[0]) score += 0.35;
    if (wantedTokens.length > 1 && candidateTokens.indexOf(wantedTokens[1]) !== -1) score += 0.2;
    return score;
  }

  function findAnchor(page, wanted) {
    var groups = lineGroups(page);
    var best = null;
    groups.forEach(function (_, start) {
      var combined = "";
      for (var count = 1; count <= 3 && start + count <= groups.length; count += 1) {
        combined += " " + groups[start + count - 1].textContent;
        var score = scoreText(combined, wanted);
        if (!best || score > best.score || (score === best.score && count < best.groups.length)) {
          best = { score: score, groups: groups.slice(start, start + count) };
        }
      }
    });
    return best && best.score >= 0.48 ? best.groups : [];
  }

  function exactSourcePrompt(page, item, fallback) {
    var wanted = item.anchor || fallback || item.prompt;
    var groups = findAnchor(page, wanted);
    if (!groups.length) return fallback || item.prompt || wanted;
    var exact = groups.map(function (group) { return group.textContent; })
      .join(" ")
      .replace(/\s+/g, " ")
      .trim();
    var exactComparison = normalize(exact).replace(/^\d+\s+/, "");
    var fallbackComparison = normalize(fallback || item.prompt || wanted).replace(/^\d+\s+/, "");
    if (exactComparison.indexOf(fallbackComparison) !== -1 || fallbackComparison.indexOf(exactComparison) !== -1) {
      return exact;
    }
    return fallback || item.prompt || wanted;
  }

  function preparePage(page) {
    if (!page || page.querySelector(":scope > .book-page-viewport")) return;
    page.classList.add("is-responsive-book-page");
    var viewport = element("div", "book-page-viewport");
    var canvas = element("div", "book-page-canvas");
    page.insertBefore(viewport, page.firstChild);
    viewport.appendChild(canvas);
    Array.prototype.slice.call(page.children).forEach(function (child) {
      if (child === viewport || child.classList.contains("page-narration-hook")) return;
      canvas.appendChild(child);
    });
  }

  function shouldSkip(item) {
    var prompt = String(item.prompt || "").trim();
    return item.type === "drawing" || /^Chora\b/i.test(prompt);
  }

  function isExplanation(prompt) {
    return /^(Eleza|Fafanua|Kwa nini|Utafanya nini|Unawezaje|Andika kwa ufupi|Andika sentensi|Tunga sentensi|Panga sentensi|Toa maelezo)\b/i.test(String(prompt || "").trim());
  }

  function accessibleName(prompt) {
    return "Jibu la swali: " + prompt;
  }

  function responseCard(prompt, id) {
    var card = element("section", "exercise-response");
    card.dataset.exerciseId = id;
    card.appendChild(element("p", "exercise-response-prompt", prompt));
    return card;
  }

  function addTextResponse(workspace, page, item) {
    var prompt = exactSourcePrompt(page, item, item.prompt);
    var card = responseCard(prompt, item.id);
    var longAnswer = item.type === "textarea";
    var control = element(longAnswer ? "textarea" : "input", longAnswer ? "exercise-response-textarea" : "exercise-response-input");
    if (longAnswer) {
      control.rows = isExplanation(prompt) ? 5 : 4;
      if (isExplanation(prompt)) control.classList.add("is-explanation");
    } else {
      control.type = "text";
    }
    control.setAttribute("aria-label", accessibleName(prompt));
    bindValue(control, item.id);
    card.appendChild(control);
    workspace.appendChild(card);
  }

  function addSelectResponse(workspace, page, item, row) {
    var id = row ? item.id + "-" + row.id : item.id;
    var seed = row ? (row.prompt || row.anchor) : item.prompt;
    var prompt = row ? seed : exactSourcePrompt(page, item, seed);
    var card = responseCard(prompt, id);
    var select = element("select", "exercise-response-select");
    var emptyOption = element("option", "", "—");
    emptyOption.value = "";
    select.appendChild(emptyOption);
    (item.options || []).forEach(function (option) {
      var optionNode = element("option", "", option);
      optionNode.value = option;
      select.appendChild(optionNode);
    });
    select.setAttribute("aria-label", accessibleName(prompt));
    bindValue(select, id);
    card.appendChild(select);
    workspace.appendChild(card);
  }

  function addRadioResponse(workspace, page, item, row, options) {
    var id = row ? item.id + "-" + row.id : item.id;
    var seed = row ? row.prompt : item.prompt;
    var prompt = row
      ? exactSourcePrompt(page, { anchor: row.prompt, prompt: row.prompt }, seed)
      : seed;
    var fieldset = element("fieldset", "exercise-response exercise-response-options");
    fieldset.dataset.exerciseId = id;
    fieldset.appendChild(element("legend", "exercise-response-prompt", prompt));
    var choices = element("div", "exercise-response-choice-list");
    var saved = stored(id);
    (options || item.options || []).forEach(function (option) {
      var label = element("label", "exercise-response-choice");
      var input = document.createElement("input");
      input.type = "radio";
      input.name = id;
      input.value = option;
      input.checked = saved === option;
      input.setAttribute("aria-label", accessibleName(prompt) + " — " + option);
      input.addEventListener("change", function () {
        if (input.checked) remember(id, option);
      });
      label.appendChild(input);
      label.appendChild(element("span", "", option));
      choices.appendChild(label);
    });
    fieldset.appendChild(choices);
    workspace.appendChild(fieldset);
  }

  function renderItem(workspace, page, item) {
    if (shouldSkip(item) || item.type === "heading") return;
    if (item.type === "matching") {
      (item.rows || []).forEach(function (row) { addSelectResponse(workspace, page, item, row); });
      return;
    }
    if (item.type === "true_false") {
      workspace.appendChild(element("p", "exercise-response-instruction", exactSourcePrompt(page, item, item.prompt)));
      (item.rows || []).forEach(function (row) {
        addRadioResponse(workspace, page, item, row, ["Kweli", "Sikweli"]);
      });
      return;
    }
    if (item.type === "radio") {
      addRadioResponse(workspace, page, item);
      return;
    }
    if (item.type === "select") {
      addSelectResponse(workspace, page, item);
      return;
    }
    addTextResponse(workspace, page, item);
  }

  function render(entry, page) {
    if (!entry || page.querySelector(":scope > .exercise-response-workspace")) return;
    var workspace = element("section", "exercise-response-workspace");
    workspace.dataset.page = pageNumber;
    workspace.setAttribute("aria-label", entry.title || "Sehemu za kujibu");
    (entry.items || []).forEach(function (item) { renderItem(workspace, page, item); });
    if (workspace.querySelector("input, textarea, select")) page.appendChild(workspace);
  }

  var page = document.querySelector(".semantic-generated-page");
  if (!page) return;
  preparePage(page);

  var manifestPromise = window.AFYA_EXERCISES
    ? Promise.resolve(window.AFYA_EXERCISES)
    : (typeof window.fetch === "function"
      ? window.fetch("./content/exercises.json?v=9").then(function (response) {
          return response.ok ? response.json() : { pages: {} };
        })
      : Promise.resolve({ pages: {} }));

  manifestPromise
    .then(function (manifest) {
      if (manifest.pages && manifest.pages[pageNumber]) render(manifest.pages[pageNumber], page);
    })
    .catch(function () { /* The complete printed page remains available if enhancement loading fails. */ });
}());
