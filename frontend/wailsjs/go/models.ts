export namespace app {
	
	export class PageDetail {
	    page?: domain.Page;
	    content: number[];
	
	    static createFrom(source: any = {}) {
	        return new PageDetail(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.page = this.convertValues(source["page"], domain.Page);
	        this.content = source["content"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class WorkspaceResult {
	    ready: boolean;
	    rootDir: string;
	    error: string;
	
	    static createFrom(source: any = {}) {
	        return new WorkspaceResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.ready = source["ready"];
	        this.rootDir = source["rootDir"];
	        this.error = source["error"];
	    }
	}

}

export namespace domain {
	
	export class Notebook {
	    id: number;
	    name: string;
	    color: string;
	
	    static createFrom(source: any = {}) {
	        return new Notebook(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.color = source["color"];
	    }
	}
	export class Page {
	    id: number;
	    section_id: number;
	    title: string;
	
	    static createFrom(source: any = {}) {
	        return new Page(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.section_id = source["section_id"];
	        this.title = source["title"];
	    }
	}
	export class Section {
	    id: number;
	    notebook_id: number;
	    name: string;
	    color: string;
	
	    static createFrom(source: any = {}) {
	        return new Section(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.notebook_id = source["notebook_id"];
	        this.name = source["name"];
	        this.color = source["color"];
	    }
	}

}

