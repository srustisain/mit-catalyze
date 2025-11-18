import axios from "axios";
import * as cheerio from "cheerio";
import { DocsStorage } from "./storage.js";

const OPENTRONS_DOCS_BASE = "https://docs.opentrons.com/v2/";
const DOCS_PAGES = [
  { path: "", title: "Welcome", section: "overview", type: "guide" as const },
  { path: "tutorial/", title: "Tutorial", section: "tutorial", type: "tutorial" as const },
  { path: "versioning/", title: "Versioning", section: "versioning", type: "guide" as const },
  { path: "labware/", title: "Labware", section: "labware", type: "api_reference" as const },
  { path: "moving-labware/", title: "Moving Labware", section: "moving-labware", type: "api_reference" as const },
  { path: "hardware-modules/", title: "Hardware Modules", section: "hardware-modules", type: "api_reference" as const },
  { path: "deck-slots/", title: "Deck Slots", section: "deck-slots", type: "api_reference" as const },
  { path: "pipettes/", title: "Pipettes", section: "pipettes", type: "api_reference" as const },
  { path: "liquid-classes/", title: "Liquid Classes", section: "liquid-classes", type: "api_reference" as const },
  { path: "building-block-commands/", title: "Building Block Commands", section: "commands", type: "api_reference" as const },
  { path: "complex-commands/", title: "Complex Commands", section: "commands", type: "api_reference" as const },
  { path: "labware-and-deck-positions/", title: "Labware and Deck Positions", section: "labware", type: "api_reference" as const },
  { path: "runtime-parameters/", title: "Runtime Parameters", section: "parameters", type: "api_reference" as const },
  { path: "advanced-control/", title: "Advanced Control", section: "advanced", type: "guide" as const },
  { path: "protocol-examples/", title: "Protocol Examples", section: "examples", type: "example" as const },
  { path: "adapting-ot-2-protocols-for-flex/", title: "Adapting OT-2 Protocols for Flex", section: "migration", type: "guide" as const },
  { path: "api-version-2-reference/", title: "API Version 2 Reference", section: "api_reference", type: "api_reference" as const },
];

export class DocsFetcher {
  private storage: DocsStorage;
  private updateIntervalHours = 24; // Check for updates daily

  constructor(storage: DocsStorage) {
    this.storage = storage;
  }

  async ensureDocsUpdated() {
    const lastUpdate = this.storage.getLastUpdateTime();
    const now = new Date();
    
    if (!lastUpdate) {
      // No docs cached, fetch them
      console.error("No cached docs found, fetching...");
      await this.fetchAndStoreDocs();
      return;
    }
    
    const hoursSinceUpdate = (now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60);
    if (hoursSinceUpdate >= this.updateIntervalHours) {
      console.error(`Docs last updated ${hoursSinceUpdate.toFixed(1)} hours ago, checking for updates...`);
      // For now, just refetch. Could optimize to check last-modified headers
      await this.fetchAndStoreDocs();
    } else {
      console.error(`Docs are up to date (last updated ${hoursSinceUpdate.toFixed(1)} hours ago)`);
    }
  }

  async fetchAndStoreDocs() {
    console.error("Fetching Opentrons Python API documentation...");
    
    // Clear existing docs
    this.storage.clearAll();
    
    let fetched = 0;
    let errors = 0;
    
    for (const page of DOCS_PAGES) {
      try {
        const url = `${OPENTRONS_DOCS_BASE}${page.path}`;
        console.error(`Fetching: ${url}`);
        
        const response = await axios.get(url, {
          timeout: 30000,
          headers: {
            "User-Agent": "Mozilla/5.0 (compatible; OpentronsDocsFetcher/1.0)",
          },
        });
        
        const $ = cheerio.load(response.data);
        
        // Extract main content
        // Remove navigation, headers, footers
        $("nav, header, footer, .sidebar, .navigation").remove();
        
        // Get main content area
        const mainContent = $("main, article, .content, #content").first();
        if (mainContent.length === 0) {
          // Fallback to body
          const body = $("body");
          body.find("nav, header, footer, script, style").remove();
          const content = body.text().trim();
          const title = $("title").text() || page.title;
          
          this.storage.insertSection(
            title,
            url,
            content,
            page.section,
            page.type
          );
        } else {
          const content = mainContent.text().trim();
          const title = $("h1").first().text() || $("title").text() || page.title;
          
          this.storage.insertSection(
            title,
            url,
            content,
            page.section,
            page.type
          );
        }
        
        // Extract code examples
        $("pre code, code").each((_, el) => {
          const code = $(el).text().trim();
          if (code.length > 50) {
            // Only store substantial code blocks
            const codeTitle = `Example: ${page.title} - ${$(el).parent().prev("h3, h4, h5").text() || "Code Example"}`;
            try {
              this.storage.insertSection(
                codeTitle,
                `${url}#example-${fetched}`,
                code,
                page.section,
                "example"
              );
            } catch (e) {
              // Ignore errors for examples
            }
          }
        });
        
        fetched++;
        
        // Rate limiting
        await new Promise((resolve) => setTimeout(resolve, 500));
      } catch (error) {
        console.error(`Error fetching ${page.path}:`, error instanceof Error ? error.message : String(error));
        errors++;
      }
    }
    
    console.error(`Fetched ${fetched} pages, ${errors} errors`);
  }
}

