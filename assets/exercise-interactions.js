(function () {
  "use strict";

  var meta = document.querySelector('meta[name="page-section-id"]');
  var pageNumber = meta ? String(Number(meta.content)) : "";
  if (!pageNumber) return;

  function element(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function storageKey(id) {
    return "afya-na-mazingira:exercise:" + pageNumber + ":" + id;
  }

  function stored(id) {
    try { return window.localStorage.getItem(storageKey(id)) || ""; }
    catch (_) { return ""; }
  }

  function remember(id, value) {
    try { window.localStorage.setItem(storageKey(id), value); }
    catch (_) { /* Controls remain usable when storage is unavailable. */ }
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
    var common = wantedTokens.filter(function (token) { return candidateTokens.indexOf(token) !== -1; }).length;
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

  function unionRect(nodes) {
    var rects = [];
    nodes.forEach(function (node) {
      var words = node.matches && node.matches(".semantic-positioned-word") ? [node] : node.querySelectorAll(".semantic-positioned-word");
      Array.prototype.forEach.call(words, function (word) {
        if (!word.classList.contains("exercise-blank-replaced")) rects.push(word.getBoundingClientRect());
      });
    });
    if (!rects.length) return null;
    return rects.reduce(function (result, rect) {
      return {
        left: Math.min(result.left, rect.left),
        top: Math.min(result.top, rect.top),
        right: Math.max(result.right, rect.right),
        bottom: Math.max(result.bottom, rect.bottom),
      };
    });
  }

  function findBlank(groups) {
    var candidates = [];
    groups.forEach(function (group) {
      Array.prototype.forEach.call(group.querySelectorAll(".semantic-positioned-word"), function (word) {
        if (/_{3,}|\.{4,}/.test(word.textContent)) candidates.push(word);
      });
    });
    candidates.sort(function (a, b) { return b.getBoundingClientRect().width - a.getBoundingClientRect().width; });
    return candidates[0] || null;
  }

  function percentRect(rect, pageRect) {
    return {
      left: (rect.left - pageRect.left) / pageRect.width * 100,
      top: (rect.top - pageRect.top) / pageRect.height * 100,
      right: (rect.right - pageRect.left) / pageRect.width * 100,
      bottom: (rect.bottom - pageRect.top) / pageRect.height * 100,
      width: rect.width / pageRect.width * 100,
    };
  }

  function positionFor(page, groups, fallbackIndex, preferWide) {
    var pageRect = page.getBoundingClientRect();
    var blank = findBlank(groups);
    if (blank) {
      var blankPosition = percentRect(blank.getBoundingClientRect(), pageRect);
      blank.classList.add("exercise-blank-replaced");
      return {
        left: Math.max(12, blankPosition.left),
        top: blankPosition.top + 0.08,
        width: Math.max(14, Math.min(72, blankPosition.width)),
        inlineBlank: true,
      };
    }

    var anchorRect = unionRect(groups);
    if (anchorRect) {
      var anchor = percentRect(anchorRect, pageRect);
      var rightSpace = 84 - anchor.right;
      if (!preferWide && rightSpace >= 15) {
        return { left: anchor.right + 0.8, top: anchor.top + 0.12, width: rightSpace, inlineBlank: false };
      }
      return {
        left: Math.max(16, Math.min(24, anchor.left)),
        top: Math.min(94, anchor.bottom + 0.08),
        width: preferWide ? 66 : 62,
        inlineBlank: false,
      };
    }

    return { left: 18, top: Math.min(91, 15 + fallbackIndex * 7), width: 64, inlineBlank: false };
  }

  function place(node, position, itemId) {
    node.style.left = position.left + "%";
    node.style.top = position.top + "%";
    node.style.width = position.width + "%";
    node.dataset.exerciseId = itemId;
    if (position.inlineBlank) node.classList.add("is-printed-blank");
  }

  function bindValue(control, id) {
    control.name = id;
    control.value = stored(id);
    control.autocomplete = "off";
    control.addEventListener("input", function () { remember(id, control.value); });
    control.addEventListener("change", function () { remember(id, control.value); });
  }

  function textControl(layer, page, item, index) {
    var groups = findAnchor(page, item.anchor || item.prompt);
    var isLong = item.type === "textarea";
    var label = element("label", "exercise-inline-control" + (isLong ? " is-long-answer" : ""));
    label.appendChild(element("span", "sr-only", item.prompt));
    var control = element(isLong ? "textarea" : "input", isLong ? "exercise-page-textarea" : "exercise-page-input");
    if (isLong) control.rows = 2;
    else control.type = "text";
    control.placeholder = isLong ? "Andika maelezo hapa" : "Andika hapa";
    control.setAttribute("aria-label", item.prompt);
    bindValue(control, item.id);
    label.appendChild(control);
    place(label, item.position || positionFor(page, groups, index, isLong || item.below), item.id);
    layer.appendChild(label);
  }

  function selectControl(layer, page, item, index, wanted, id, replaceAnchor) {
    var groups = findAnchor(page, wanted || item.anchor || item.prompt);
    var label = element("label", "exercise-inline-control");
    label.appendChild(element("span", "sr-only", wanted || item.prompt));
    var select = element("select", "exercise-page-select");
    var placeholder = element("option", "", "Chagua jibu");
    placeholder.value = "";
    select.appendChild(placeholder);
    (item.options || []).forEach(function (option) {
      var optionNode = element("option", "", option);
      optionNode.value = option;
      select.appendChild(optionNode);
    });
    select.setAttribute("aria-label", wanted || item.prompt);
    bindValue(select, id || item.id);
    label.appendChild(select);
    var position;
    if (replaceAnchor && groups.length) {
      var pageRect = page.getBoundingClientRect();
      var anchorRect = unionRect(groups);
      var anchorPosition = percentRect(anchorRect, pageRect);
      groups.forEach(function (group) {
        Array.prototype.forEach.call(group.querySelectorAll(".semantic-positioned-word"), function (word) {
          word.classList.add("exercise-blank-replaced");
        });
      });
      position = {
        left: anchorPosition.left,
        top: anchorPosition.top + 0.08,
        width: Math.max(24, Math.min(42, 84 - anchorPosition.left)),
        inlineBlank: true,
      };
    } else {
      position = positionFor(page, groups, index, false);
    }
    place(label, position, id || item.id);
    layer.appendChild(label);
  }

  function radioControl(layer, page, item, index, wanted, id, options, preferWide) {
    var groups = findAnchor(page, wanted || item.anchor || item.prompt);
    var wrapper = element("fieldset", "exercise-inline-options");
    wrapper.appendChild(element("legend", "sr-only", wanted || item.prompt));
    var saved = stored(id || item.id);
    (options || item.options || []).forEach(function (option) {
      var label = element("label", "exercise-page-radio");
      var input = document.createElement("input");
      input.type = "radio";
      input.name = id || item.id;
      input.value = option;
      input.checked = saved === option;
      input.addEventListener("change", function () { if (input.checked) remember(id || item.id, option); });
      label.appendChild(input);
      label.appendChild(element("span", "", option));
      wrapper.appendChild(label);
    });
    var position = item.position || positionFor(page, groups, index, preferWide !== false);
    if (!item.position && preferWide === false && position.left < 30 && groups.length) {
      var pageRect = page.getBoundingClientRect();
      var anchor = percentRect(unionRect(groups), pageRect);
      position = { left: 64, top: anchor.bottom + 0.08, width: 20, inlineBlank: false };
    }
    place(wrapper, position, id || item.id);
    layer.appendChild(wrapper);
  }

  function addRemainingPrintedBlanks(layer, page) {
    Array.prototype.forEach.call(page.querySelectorAll(".semantic-positioned-word"), function (word) {
      if (word.classList.contains("exercise-blank-replaced") || !(/_{3,}|\.{4,}/.test(word.textContent))) return;
      var group = word.closest(".semantic-text-group");
      var prompt = group ? group.textContent.replace(/_{3,}|\.{4,}/g, " nafasi ").trim() : "Jaza nafasi";
      var id = "p" + pageNumber + "-blank-" + (word.dataset.wordIndex || Math.round(word.offsetTop));
      var label = element("label", "exercise-inline-control is-printed-blank");
      label.appendChild(element("span", "sr-only", prompt));
      var input = element("input", "exercise-page-input");
      input.type = "text";
      input.placeholder = "Jibu";
      input.setAttribute("aria-label", prompt);
      bindValue(input, id);
      label.appendChild(input);
      var pageRect = page.getBoundingClientRect();
      var blank = percentRect(word.getBoundingClientRect(), pageRect);
      word.classList.add("exercise-blank-replaced");
      place(label, {
        left: Math.max(12, blank.left),
        top: blank.top + 0.08,
        width: Math.max(14, Math.min(72, blank.width)),
        inlineBlank: true,
      }, id);
      layer.appendChild(label);
    });
  }

  function stackedField(item, prompt) {
    if (item.type === "heading") {
      var heading = element("div", "exercise-reflow-row is-heading");
      heading.appendChild(element("span", "exercise-reflow-prompt", prompt));
      return heading;
    }
    var label = element("label", "exercise-reflow-row");
    label.dataset.exerciseId = item.id;
    label.appendChild(element("span", "exercise-reflow-prompt", prompt));
    var control;
    if (item.type === "true_false_row") {
      control = element("span", "exercise-reflow-choices");
      var saved = stored(item.id);
      ["Kweli", "Sikweli"].forEach(function (option) {
        var choice = element("span", "exercise-reflow-choice");
        var radio = document.createElement("input");
        radio.type = "radio";
        radio.name = item.id;
        radio.value = option;
        radio.checked = saved === option;
        radio.addEventListener("change", function () { if (radio.checked) remember(item.id, option); });
        choice.appendChild(radio);
        choice.appendChild(element("span", "", option));
        control.appendChild(choice);
      });
    } else if (item.type === "select") {
      control = element("select", "exercise-reflow-input");
      var placeholder = element("option", "", "Chagua jibu");
      placeholder.value = "";
      control.appendChild(placeholder);
      (item.options || []).forEach(function (option) {
        var optionNode = element("option", "", option);
        optionNode.value = option;
        control.appendChild(optionNode);
      });
    } else {
      control = element(item.type === "textarea" ? "textarea" : "input", item.type === "textarea" ? "exercise-reflow-textarea" : "exercise-reflow-input");
      if (item.type === "textarea") control.rows = 2;
      else control.type = "text";
      control.placeholder = "Andika jibu hapa";
    }
    control.setAttribute("aria-label", prompt);
    if (item.type !== "true_false_row") bindValue(control, item.id);
    label.appendChild(control);
    return label;
  }

  function renderStacked(entry, layer, page) {
    var pageRect = page.getBoundingClientRect();
    var anchored = [];
    var stackItems = [];
    (entry.items || []).forEach(function (item) {
      if (item.type === "true_false") {
        stackItems.push({
          id: item.id + "-heading",
          type: "heading",
          prompt: item.prompt,
          anchor: item.prompt,
        });
        (item.rows || []).forEach(function (row) {
          stackItems.push({
            id: item.id + "-" + row.id,
            type: "true_false_row",
            prompt: row.prompt,
            anchor: row.prompt,
          });
        });
      } else {
        stackItems.push(item);
      }
    });
    stackItems.forEach(function (item) {
      var groups = findAnchor(page, item.anchor || item.prompt);
      var rect = unionRect(groups);
      if (!groups.length || !rect || item.type === "matching" || item.type === "radio") return;
      var position = percentRect(rect, pageRect);
      var prompt = groups.map(function (group) { return group.textContent; }).join(" ").replace(/\s+/g, " ").trim();
      groups.forEach(function (group) {
        group.classList.add("exercise-reflow-source");
        group.setAttribute("aria-hidden", "true");
      });
      anchored.push({ item: item, groups: groups, prompt: prompt, position: position });
    });
    anchored.sort(function (a, b) { return a.position.top - b.position.top; });

    var sections = [];
    anchored.forEach(function (answer) {
      var section = sections[sections.length - 1];
      if (!section || answer.position.top - section[section.length - 1].position.top > 5.4) {
        section = [];
        sections.push(section);
      }
      section.push(answer);
    });

    sections.forEach(function (answers) {
      var panel = element("section", "exercise-reflow-panel");
      var top = Math.max(4, answers[0].position.top - 0.28);
      var left = Math.max(8, Math.min.apply(null, answers.map(function (answer) { return answer.position.left; })) - 0.4);
      var height = answers.reduce(function (total, answer) {
        if (answer.item.type === "heading") return total + 1.65;
        return total + (answer.item.type === "textarea" ? 3.15 : 2.72);
      }, 0);
      panel.style.left = left + "%";
      panel.style.top = top + "%";
      panel.style.width = Math.max(54, 84.5 - left) + "%";
      panel.style.height = height + "%";
      answers.forEach(function (answer) {
        panel.appendChild(stackedField(answer.item, answer.prompt));
      });
      layer.appendChild(panel);
    });
  }

  function render(entry) {
    var page = document.querySelector(".semantic-page");
    if (!page || page.querySelector(".exercise-page-layer")) return;
    var layer = element("div", "exercise-page-layer");
    layer.setAttribute("aria-label", entry.title || "Sehemu za kujibu");
    layer.dataset.page = pageNumber;
    page.appendChild(layer);

    if (entry.layout === "stacked") {
      renderStacked(entry, layer, page);
      return;
    }

    (entry.items || []).forEach(function (item, index) {
      if (item.type === "matching") {
        (item.rows || []).forEach(function (row, rowIndex) {
          selectControl(layer, page, item, index + rowIndex, row.anchor || row.prompt, item.id + "-" + row.id, row.replace);
        });
      } else if (item.type === "true_false") {
        (item.rows || []).forEach(function (row, rowIndex) {
          radioControl(layer, page, item, index + rowIndex, row.prompt, item.id + "-" + row.id, ["Kweli", "Sikweli"], false);
        });
      } else if (item.type === "radio") {
        radioControl(layer, page, item, index);
      } else if (item.type === "select") {
        selectControl(layer, page, item, index);
      } else {
        textControl(layer, page, item, index);
      }
    });
    addRemainingPrintedBlanks(layer, page);
  }

  var manifestPromise = window.AFYA_EXERCISES
    ? Promise.resolve(window.AFYA_EXERCISES)
    : (typeof window.fetch === "function"
      ? window.fetch("./content/exercises.json?v=8").then(function (response) {
          return response.ok ? response.json() : { pages: {} };
        })
      : Promise.resolve({ pages: {} }));

  manifestPromise
    .then(function (manifest) {
      if (manifest.pages && manifest.pages[pageNumber]) render(manifest.pages[pageNumber]);
    })
    .catch(function () { /* The printed page remains available if enhancement loading fails. */ });
}());
