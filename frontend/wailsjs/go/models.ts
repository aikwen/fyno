export namespace app {
	
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

