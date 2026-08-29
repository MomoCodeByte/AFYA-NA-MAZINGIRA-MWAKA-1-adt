(function () {
  "use strict";

  var BOOK_ID = "AFYA-NA-MAZINGIRA-MWAKA-1-adt";
  var pageMeta = document.querySelector('meta[name="page-section-id"]');
  var titleMeta = document.querySelector('meta[name="title-id"]');
  var pageNumber = pageMeta ? String(Number(pageMeta.content)) : "";
  var sectionId = titleMeta ? titleMeta.content : "page-" + pageNumber;
  var sourceCardMap = new WeakMap();
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

  function sourceInfo(page, item, fallback, allowAnchorOnly) {
    var wanted = item.anchor || fallback || item.prompt;
    var groups = findAnchor(page, wanted);
    if (!groups.length) {
      return { prompt: fallback || item.prompt || wanted, groups: [] };
    }
    var exact = groups.map(function (group) { return group.textContent; })
      .join(" ")
      .replace(/\s+/g, " ")
      .trim();
    var exactComparison = normalize(exact).replace(/^\d+\s+/, "");
    var fallbackComparison = normalize(fallback || item.prompt || wanted).replace(/^\d+\s+/, "");
    var verified = allowAnchorOnly || exactComparison.indexOf(fallbackComparison) !== -1 || fallbackComparison.indexOf(exactComparison) !== -1;
    return {
      prompt: verified ? exact : (fallback || item.prompt || wanted),
      groups: groups,
      verified: verified,
    };
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

  function sourceQuestion(card, info) {
    if (!info.groups.length) {
      card.classList.add("has-no-source-question");
      return;
    }
    var source = element("div", "exercise-source-question");
    info.groups.forEach(function (group) {
      group.classList.add("exercise-source-group");
      source.appendChild(group);
    });
    card.appendChild(source);
  }

  function responseCard(workspace, info, id) {
    var existing = null;
    info.groups.some(function (group) {
      existing = sourceCardMap.get(group) || null;
      return Boolean(existing);
    });
    if (existing) return existing;
    var card = element("section", "exercise-response");
    card.dataset.exerciseId = id;
    sourceQuestion(card, info);
    info.groups.forEach(function (group) { sourceCardMap.set(group, card); });
    workspace.appendChild(card);
    return card;
  }

  function unionRect(nodes) {
    var rects = [];
    nodes.forEach(function (node) {
      var words = node.matches && node.matches(".semantic-positioned-word")
        ? [node]
        : node.querySelectorAll(".semantic-positioned-word");
      Array.prototype.forEach.call(words, function (word) { rects.push(word.getBoundingClientRect()); });
    });
    if (!rects.length) return null;
    return rects.reduce(function (result, rect) {
      return {
        left: Math.min(result.left, rect.left),
        top: Math.min(result.top, rect.top),
        right: Math.max(result.right, rect.right),
        bottom: Math.max(result.bottom, rect.bottom),
        width: Math.max(result.right, rect.right) - Math.min(result.left, rect.left),
        height: Math.max(result.bottom, rect.bottom) - Math.min(result.top, rect.top),
      };
    });
  }

  function inlineLayer(page) {
    var canvas = page.querySelector(".book-page-canvas");
    var layer = canvas.querySelector(".exercise-inline-answer-layer");
    if (!layer) {
      layer = element("div", "exercise-inline-answer-layer");
      canvas.appendChild(layer);
    }
    return layer;
  }

  function printedBlank(groups) {
    var answer = null;
    groups.some(function (group) {
      return Array.prototype.some.call(group.querySelectorAll(".semantic-positioned-word"), function (word) {
        if (!word.classList.contains("exercise-printed-blank") && /_{3,}|\.{4,}/.test(word.textContent)) {
          answer = word;
          return true;
        }
        return false;
      });
    });
    return answer;
  }

  function placeInlineControl(page, targetNodes, control, id, replaceAllWords) {
    var canvas = page.querySelector(".book-page-canvas");
    var canvasRect = canvas.getBoundingClientRect();
    var targetRect = unionRect(targetNodes);
    if (!targetRect || !canvasRect.width) return false;
    var wrapper = element("label", "exercise-inline-answer-control");
    wrapper.dataset.exerciseId = id;
    wrapper.style.left = ((targetRect.left - canvasRect.left) / canvasRect.width * 100) + "%";
    wrapper.style.top = ((targetRect.top - canvasRect.top) / canvasRect.height * 100) + "%";
    var baseWidth = targetRect.width / canvasRect.width * 100;
    wrapper.style.width = Math.min(72, Math.max(replaceAllWords ? 26 : 14, baseWidth)) + "%";
    wrapper.appendChild(control);
    inlineLayer(page).appendChild(wrapper);
    targetNodes.forEach(function (node) {
      var words = node.matches && node.matches(".semantic-positioned-word")
        ? [node]
        : node.querySelectorAll(".semantic-positioned-word");
      Array.prototype.forEach.call(words, function (word) {
        word.classList.add("exercise-printed-blank");
        word.setAttribute("aria-hidden", "true");
      });
    });
    return true;
  }

  function placeManifestControl(page, position, control, id) {
    if (!position) return false;
    var wrapper = element("label", "exercise-inline-answer-control");
    wrapper.dataset.exerciseId = id;
    wrapper.style.left = position.left + "%";
    wrapper.style.top = position.top + "%";
    wrapper.style.width = position.width + "%";
    wrapper.appendChild(control);
    inlineLayer(page).appendChild(wrapper);
    return true;
  }

  function placeBelowSourceControl(page, groups, control, id) {
    var canvas = page.querySelector(".book-page-canvas");
    var canvasRect = canvas.getBoundingClientRect();
    var sourceRect = unionRect(groups);
    if (!sourceRect || !canvasRect.width) return false;
    var left = (sourceRect.left - canvasRect.left) / canvasRect.width * 100;
    var wrapper = element("label", "exercise-inline-answer-control is-table-answer");
    wrapper.dataset.exerciseId = id;
    wrapper.style.left = left + "%";
    wrapper.style.top = (((sourceRect.bottom - canvasRect.top) / canvasRect.height * 100) + 0.2) + "%";
    wrapper.style.width = Math.max(28, Math.min(42, 56 - left)) + "%";
    wrapper.appendChild(control);
    inlineLayer(page).appendChild(wrapper);
    return true;
  }

  function textControl(item, prompt) {
    var longAnswer = item.type === "textarea";
    var control = element(longAnswer ? "textarea" : "input", longAnswer ? "exercise-response-textarea" : "exercise-response-input");
    if (longAnswer) {
      control.rows = isExplanation(prompt) ? 5 : 4;
      if (isExplanation(prompt)) control.classList.add("is-explanation");
    } else {
      control.type = "text";
    }
    control.setAttribute("aria-label", accessibleName(prompt));
    control.dataset.exerciseId = item.id;
    bindValue(control, item.id);
    return control;
  }

  function addTextResponse(workspace, page, item) {
    var info = sourceInfo(page, item, item.prompt, false);
    var control = textControl(item, info.prompt);
    if (item.position && placeManifestControl(page, item.position, control, item.id)) return;
    var blank = item.type !== "textarea" ? printedBlank(info.groups) : null;
    if (blank && placeInlineControl(page, [blank], control, item.id, false)) {
      return;
    }
    var card = responseCard(workspace, info, item.id);
    card.appendChild(control);
  }

  function selectControl(item, id, prompt) {
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
    select.dataset.exerciseId = id;
    bindValue(select, id);
    return select;
  }

  function addSelectResponse(workspace, page, item, row) {
    var id = row ? item.id + "-" + row.id : item.id;
    var seed = row ? (row.prompt || row.anchor) : item.prompt;
    if (row && pageNumber === "13") {
      var answerGroups = findAnchor(page, row.anchor);
      var inlineSelect = selectControl(item, id, seed);
      if (answerGroups.length && placeInlineControl(page, answerGroups, inlineSelect, id, true)) return;
    }
    if (row && pageNumber === "50" && window.innerWidth > 480) {
      var questionGroups = findAnchor(page, row.prompt);
      var tableSelect = selectControl(item, id, seed);
      if (questionGroups.length && placeBelowSourceControl(page, questionGroups, tableSelect, id)) return;
    }
    var info = sourceInfo(page, { anchor: row ? row.prompt : item.anchor, prompt: seed }, seed, false);
    var select = selectControl(item, id, info.prompt);
    var blank = printedBlank(info.groups);
    if (blank && placeInlineControl(page, [blank], select, id, false)) return;
    var card = responseCard(workspace, info, id);
    card.appendChild(select);
  }

  function addRadioResponse(workspace, page, item, row, options) {
    var id = row ? item.id + "-" + row.id : item.id;
    var seed = row ? row.prompt : item.prompt;
    var lookup = row ? { anchor: row.prompt, prompt: row.prompt } : item;
    var info = sourceInfo(page, lookup, seed, !row && Boolean(item.anchor));
    var card = responseCard(workspace, info, id);
    card.classList.add("exercise-response-options");
    var choices = element("div", "exercise-response-choice-list");
    var saved = stored(id);
    (options || item.options || []).forEach(function (option) {
      var label = element("label", "exercise-response-choice");
      var input = document.createElement("input");
      input.type = "radio";
      input.name = id;
      input.value = option;
      input.checked = saved === option;
      input.setAttribute("aria-label", accessibleName(info.prompt) + " — " + option);
      input.addEventListener("change", function () {
        if (input.checked) remember(id, option);
      });
      label.appendChild(input);
      label.appendChild(element("span", "", option));
      choices.appendChild(label);
    });
    card.appendChild(choices);
  }

  function renderItem(workspace, page, item) {
    if (shouldSkip(item) || item.type === "heading") return;
    if (item.type === "matching") {
      (item.rows || []).forEach(function (row) { addSelectResponse(workspace, page, item, row); });
      return;
    }
    if (item.type === "true_false") {
      var instructionInfo = sourceInfo(page, item, item.prompt, false);
      if (instructionInfo.groups.length) {
        var instruction = element("div", "exercise-source-instruction");
        instructionInfo.groups.forEach(function (group) {
          group.classList.add("exercise-source-group");
          instruction.appendChild(group);
        });
        workspace.appendChild(instruction);
      }
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

  function groupTop(group) {
    var word = group.querySelector(".semantic-positioned-word");
    return word ? (parseFloat(word.style.top) || 0) : 0;
  }

  function finalizeStackedFlow(entry, page, workspace, originalGroups) {
    if (entry.layout !== "stacked") return;
    var movedGroups = Array.prototype.slice.call(workspace.querySelectorAll(".exercise-source-group"));
    if (!movedGroups.length) return;
    var movedOrders = movedGroups.map(function (group) {
      return Number(group.dataset.exerciseSourceOrder);
    }).filter(function (order) { return Number.isFinite(order); });
    if (!movedOrders.length) return;
    var start = Math.min.apply(null, movedOrders);
    var end = Math.max.apply(null, movedOrders);
    while (start > 0) {
      var previous = originalGroups[start - 1];
      var previousText = normalize(previous.textContent);
      if (!/^H[1-6]$/.test(previous.tagName) && !/^(maswali|zoezi|jibu|kazi ya kufanya)\b/.test(previousText)) break;
      start -= 1;
    }

    originalGroups.forEach(function (group, order) {
      group.dataset.exerciseSourceOrder = String(order);
      if (order < start || order > end || group.closest(".exercise-response-workspace") || group.querySelector(".exercise-printed-blank")) return;
      var context = element("div", "exercise-source-context");
      context.dataset.flowOrder = String(order);
      group.classList.add("exercise-source-group");
      context.appendChild(group);
      workspace.appendChild(context);
    });

    Array.prototype.forEach.call(workspace.children, function (child, index) {
      if (child.dataset.flowOrder) return;
      var orders = Array.prototype.slice.call(child.querySelectorAll(".exercise-source-group")).map(function (group) {
        return Number(group.dataset.exerciseSourceOrder);
      }).filter(function (order) { return Number.isFinite(order); });
      child.dataset.flowOrder = orders.length ? String(Math.min.apply(null, orders)) : String(10000 + index);
    });
    Array.prototype.slice.call(workspace.children)
      .sort(function (a, b) { return Number(a.dataset.flowOrder) - Number(b.dataset.flowOrder); })
      .forEach(function (child) { workspace.appendChild(child); });

    var cropTop = groupTop(originalGroups[start]);
    var viewport = page.querySelector(".book-page-viewport");
    var canvas = page.querySelector(".book-page-canvas");
    if (cropTop <= 3) {
      viewport.hidden = true;
      return;
    }
    var cropRatio = Math.max(0.02, (cropTop - 1.25) / 100);
    canvas.classList.add("is-cropped");
    canvas.style.setProperty("--book-crop-ratio", String(cropRatio));
    canvas.style.aspectRatio = "900 / " + (1239 * cropRatio);
  }

  function render(entry, page) {
    if (!entry || page.querySelector(":scope > .exercise-response-workspace")) return;
    var originalGroups = lineGroups(page);
    originalGroups.forEach(function (group, order) {
      group.dataset.exerciseSourceOrder = String(order);
    });
    var workspace = element("section", "exercise-response-workspace");
    workspace.dataset.page = pageNumber;
    workspace.setAttribute("aria-label", entry.title || "Sehemu za kujibu");
    (entry.items || []).forEach(function (item) { renderItem(workspace, page, item); });
    finalizeStackedFlow(entry, page, workspace, originalGroups);
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
